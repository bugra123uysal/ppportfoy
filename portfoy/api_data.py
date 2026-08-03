"""Query functions backing the JSON API's read endpoints (see api/index.py).

Each function returns plain dataclasses/dicts rather than anything
framework-specific, and is kept here (not in api/) so it stays unit-testable
with plain pytest -- no Flask, no HTTP, no Vercel involved.

Mutations (add/remove position) go through storage.py directly from
api/index.py instead of living here -- see that module's docstring for how
writes survive Vercel's read-only filesystem (Upstash, when configured).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from . import config, data, performance, risk, storage
from .breadth import BreadthSnapshot, build_snapshot
from .calendar_events import MarketEvent, upcoming_events
from .indicators import last_value, sma
from .money_flow import build_money_flow_scan
from .options import OptionActivity, rank_by_volume
from .performance import SeriesResult
from .risk import PositionMetrics
from .rotation import build_rotation, build_sector_leaders
from .sentiment import SentimentScore, build_score
from .trade_scan import build_trade_scan


def _load_metrics() -> tuple[list[PositionMetrics], list[storage.CashHolding], float | None]:
    """Positions + cash + live metrics -- the common core of most endpoints."""
    positions = storage.load_portfolio()
    cash = storage.load_cash()
    symbols = tuple(p.symbol for p in positions)
    quotes = data.get_quotes(symbols) if symbols else {}
    histories = {sym: data.get_history(sym) for sym in symbols}
    usdtry = data.get_usdtry()
    cash_usd = risk.cash_totals(cash, usdtry)["usd"]
    metrics = risk.compute_metrics(positions, quotes, histories, usdtry, cash_usd)
    return metrics, cash, usdtry


def positions_payload() -> dict:
    metrics, cash, usdtry = _load_metrics()
    return {"metrics": metrics, "cash": cash, "usdtry": usdtry}


def portfolio_summary_payload() -> dict:
    metrics, cash, usdtry = _load_metrics()
    macro = data.get_macro_snapshot()
    vix = next((row["price"] for row in macro if row["symbol"] == "^VIX"), None)
    earnings = {
        m.symbol: (data.get_next_earnings(m.symbol) if not m.symbol.endswith(".IS") else None)
        for m in metrics
    }
    totals = risk.portfolio_totals(metrics, usdtry, cash)
    alerts = risk.build_alerts(metrics, earnings, vix)
    return {"totals": totals, "alerts": alerts}


def portfolio_history_payload() -> list[dict]:
    return storage.load_history()


def rotation_payload(include_mine: bool = False) -> dict:
    symbols = [config.RRG_BENCHMARK, *config.SECTOR_ETFS]
    labels = dict(config.SECTOR_ETFS)
    if include_mine:
        positions = storage.load_portfolio()
        mine = [
            p.symbol for p in positions
            if not p.symbol.endswith(".IS") and p.symbol not in symbols
        ]
        symbols.extend(mine)
        labels.update({sym: ("Portföyüm", "My holding") for sym in mine})
    leader_symbols = [sym for stocks in config.SECTOR_LEADER_STOCKS.values() for sym in stocks]
    closes = data.get_weekly_closes(tuple(dict.fromkeys([*symbols, *leader_symbols])))
    if closes.empty:
        return {"sectors": [], "leaders": {}}
    sectors = build_rotation(closes, labels, reference=list(config.SECTOR_ETFS))
    leaders = build_sector_leaders(closes, config.SECTOR_LEADER_STOCKS)
    return {"sectors": sectors, "leaders": leaders}


def _sector_leader_universe() -> dict[str, str]:
    """SECTOR_LEADER_STOCKS flattened to ticker -> Turkish sector label."""
    return {
        stock: config.SECTOR_ETFS[sector_etf][0]
        for sector_etf, stocks in config.SECTOR_LEADER_STOCKS.items()
        for stock in stocks
    }


def trade_scan_payload() -> dict:
    return {"signals": build_trade_scan(_sector_leader_universe())}


def money_flow_payload() -> dict:
    return {"signals": build_money_flow_scan(_sector_leader_universe())}


def option_activity_payload(symbol: str) -> OptionActivity | None:
    return data.get_option_activity(symbol)


def options_scan_payload() -> list[OptionActivity]:
    positions = storage.load_portfolio()
    own_us = [p.symbol for p in positions if not p.symbol.endswith(".IS")]
    universe = list(dict.fromkeys([*config.OPTIONS_UNIVERSE, *own_us]))
    results = [data.get_option_activity(sym) for sym in universe]
    return rank_by_volume([a for a in results if a is not None])


def breadth_payload() -> BreadthSnapshot | None:
    closes = data.get_daily_closes(config.BREADTH_UNIVERSE)
    return build_snapshot(closes)


def sentiment_payload() -> SentimentScore | None:
    macro = data.get_macro_snapshot()
    vix = next((row["price"] for row in macro if row["symbol"] == "^VIX"), None)
    spx = data.get_history("^GSPC")
    price = last_value(spx["Close"]) if not spx.empty else None
    spx_sma = last_value(sma(spx["Close"], config.SENT_MOMENTUM_SMA)) if not spx.empty else None
    spy_options = data.get_option_activity("SPY")
    put_call = spy_options.put_call_ratio if spy_options else None
    snapshot = breadth_payload()
    pct_200 = snapshot.pct_above_200 if snapshot else None
    return build_score(vix=vix, price=price, sma=spx_sma, pct_above_200=pct_200, put_call=put_call)


def macro_payload() -> list[dict]:
    return data.get_macro_snapshot()


def calendar_payload(days: int = config.CALENDAR_LOOKAHEAD_DAYS) -> list[MarketEvent]:
    positions = storage.load_portfolio()
    earnings = {
        p.symbol: data.get_next_earnings(p.symbol)
        for p in positions if not p.symbol.endswith(".IS")
    }
    return upcoming_events(date.today(), earnings, days)


def news_payload(symbol: str, lang: str = "tr") -> list[dict]:
    from . import news

    return news.get_news_for(symbol, lang)


def compare_payload(
    period: str = config.DEFAULT_COMPARE_PERIOD, base: str = "USD"
) -> list[SeriesResult]:
    metrics, cash, usdtry = _load_metrics()
    prices = {}
    for m in metrics:
        hist = data.get_history(m.symbol, config.COMPARE_HISTORY_PERIOD)
        if not hist.empty:
            prices[m.symbol] = hist["Close"]
    benchmarks = {}
    for sym in config.BENCHMARKS:
        hist = data.get_history(sym, config.COMPARE_HISTORY_PERIOD)
        if not hist.empty:
            benchmarks[sym] = hist["Close"]
    fx_hist = data.get_history(config.FX_USDTRY, config.COMPARE_HISTORY_PERIOD)
    fx_series = fx_hist["Close"] if not fx_hist.empty else pd.Series(dtype=float)
    if base == "TRY" and fx_series.empty:
        return []

    reference = next(iter(benchmarks.values()), None)
    start = (
        performance.window_start(performance.to_daily(reference).index, period)
        if reference is not None
        else None
    )
    totals = risk.portfolio_totals(metrics, usdtry, cash)
    portfolio = performance.portfolio_series(
        weights={m.symbol: m.weight for m in metrics},
        prices=prices,
        currencies={m.symbol: m.currency for m in metrics},
        base=base,
        usdtry=fx_series,
        start=start,
        cash_weight=totals.get("cash_weight", 0.0),
    )
    return performance.compare(portfolio, benchmarks, base, fx_series, period)
