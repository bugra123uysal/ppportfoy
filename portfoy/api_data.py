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
from .commentary import (
    market_pulse_commentary,
    rotation_commentary,
    stage_commentary,
    symbol_report_commentary,
)
from .data import AnalystView
from .indicators import last_value, sma
from .options import OptionActivity, rank_by_volume
from .performance import SeriesResult
from .position_health import evaluate_portfolio
from .report import SymbolContext, SymbolReport, build_report, build_symbol_context
from .risk import PositionMetrics
from .rotation import build_rotation, build_sector_leaders
from .sentiment import SentimentScore, build_score
from .stage_analysis import StageAnalysis, build_stage_scan
from .yield_curve import YieldCurveSnapshot, build_yield_curve_snapshot, credit_spread_proxy_change


def _load_metrics() -> tuple[
    list[PositionMetrics], list[storage.CashHolding], float | None, dict[str, pd.DataFrame]
]:
    """Positions + cash + live metrics -- the common core of most endpoints.

    Also returns the fetched `histories` so callers that need per-symbol
    price history for something else (see position_health_payload) can reuse
    it instead of a second `get_histories` round trip.
    """
    positions = storage.load_portfolio()
    cash = storage.load_cash()
    symbols = tuple(p.symbol for p in positions)
    quotes = data.get_quotes(symbols) if symbols else {}
    histories = data.get_histories(symbols) if symbols else {}
    usdtry = data.get_usdtry()
    cash_usd = risk.cash_totals(cash, usdtry)["usd"]
    metrics = risk.compute_metrics(positions, quotes, histories, usdtry, cash_usd)
    return metrics, cash, usdtry, histories


def positions_payload() -> dict:
    metrics, cash, usdtry, _histories = _load_metrics()
    return {"metrics": metrics, "cash": cash, "usdtry": usdtry}


def portfolio_summary_payload() -> dict:
    metrics, cash, usdtry, histories = _load_metrics()
    macro = data.get_macro_snapshot()
    vix = next((row["price"] for row in macro if row["symbol"] == "^VIX"), None)
    earnings = {
        m.symbol: (data.get_next_earnings(m.symbol) if not m.symbol.endswith(".IS") else None)
        for m in metrics
    }
    totals = risk.portfolio_totals(metrics, usdtry, cash)
    alerts = risk.build_alerts(metrics, earnings, vix)
    position_health = evaluate_portfolio([m.symbol for m in metrics], histories)
    return {"totals": totals, "alerts": alerts, "position_health": position_health}


def portfolio_history_payload() -> list[dict]:
    return storage.load_history()


def stage_payload() -> dict:
    """Weinstein 4-stage read for every current holding (Evre Takibi) --
    needs its own, longer history fetch (STAGE_ANALYSIS_PERIOD) since a
    30-week SMA needs far more lead-in than the 1y default _load_metrics
    fetches for live P&L."""
    positions = storage.load_portfolio()
    symbols = tuple(p.symbol for p in positions)
    if not symbols:
        return {"stages": [], "commentary": None}
    histories = data.get_histories(symbols, config.STAGE_ANALYSIS_PERIOD)
    bench_symbols = tuple(dict.fromkeys(config.STAGE_BENCHMARKS.values()))
    benchmarks = data.get_histories(bench_symbols, config.STAGE_ANALYSIS_PERIOD)
    stages: list[StageAnalysis] = build_stage_scan(list(symbols), histories, benchmarks)
    return {"stages": stages, "commentary": stage_commentary(stages)}


def _sector_and_leader_symbols() -> tuple[list[str], list[str]]:
    """(benchmark + sector ETF symbols, flattened leader-pool symbols) --
    the two symbol groups every rotation-scoring weekly-closes fetch needs.
    """
    return (
        [config.RRG_BENCHMARK, *config.SECTOR_ETFS],
        [sym for stocks in config.SECTOR_LEADER_STOCKS.values() for sym in stocks],
    )


def rotation_payload(include_mine: bool = False) -> dict:
    symbols, leader_symbols = _sector_and_leader_symbols()
    labels = dict(config.SECTOR_ETFS)
    if include_mine:
        positions = storage.load_portfolio()
        mine = [
            p.symbol for p in positions
            if not p.symbol.endswith(".IS") and p.symbol not in symbols
        ]
        symbols.extend(mine)
        labels.update({sym: ("Portföyüm", "My holding") for sym in mine})
    closes = data.get_weekly_closes(tuple(dict.fromkeys([*symbols, *leader_symbols])))
    if closes.empty:
        return {"sectors": [], "leaders": {}, "commentary": None}
    sectors = build_rotation(closes, labels, reference=list(config.SECTOR_ETFS))
    leaders = build_sector_leaders(closes, config.SECTOR_LEADER_STOCKS)
    # Commentary reads only the actual sector ETFs -- when include_mine=True,
    # `sectors` also carries the user's own individual holdings, which would
    # read like extra sectors to the model.
    etf_sectors = [s for s in sectors if s.symbol in config.SECTOR_ETFS]
    return {
        "sectors": sectors,
        "leaders": leaders,
        "commentary": rotation_commentary(etf_sectors),
    }


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
    if closes.empty:
        return None
    volumes = data.get_daily_volumes(config.BREADTH_UNIVERSE)
    return build_snapshot(closes, volumes if not volumes.empty else None)


def yield_curve_payload() -> YieldCurveSnapshot:
    quotes = data.get_quotes((config.YIELD_10Y_TICKER, config.YIELD_3M_TICKER))
    y10 = quotes.get(config.YIELD_10Y_TICKER)
    y3m = quotes.get(config.YIELD_3M_TICKER)
    hy = data.get_history(config.CREDIT_HY_TICKER, period="3mo")
    ig = data.get_history(config.CREDIT_IG_TICKER, period="3mo")
    credit_change = (
        credit_spread_proxy_change(hy["Close"], ig["Close"])
        if not hy.empty and not ig.empty
        else None
    )
    return build_yield_curve_snapshot(
        yield_10y=y10.price if y10 else None,
        yield_3m=y3m.price if y3m else None,
        credit_change_pct=credit_change,
    )


def analyst_payload() -> dict[str, AnalystView]:
    """Analyst price targets/consensus for the user's US-listed holdings --
    Yahoo doesn't cover BIST (.IS) names here, same exclusion as earnings."""
    positions = storage.load_portfolio()
    us_symbols = [p.symbol for p in positions if not p.symbol.endswith(".IS")]
    out: dict[str, AnalystView] = {}
    for sym in us_symbols:
        view = data.get_analyst_view(sym)
        if view is not None:
            out[sym] = view
    return out


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


def market_pulse_payload() -> dict:
    """Piyasa Pusulası's headline AI digest -- reuses the same breadth/
    sentiment/yield-curve/macro payload functions the page's other panels
    already call, so this makes no extra network round trip beyond what
    those functions themselves need (each is independently cached, see
    config.py's *_CACHE_TTL constants)."""
    breadth = breadth_payload()
    sentiment = sentiment_payload()
    yield_curve = yield_curve_payload()
    macro = macro_payload()
    return {
        "commentary": market_pulse_commentary(breadth, sentiment, yield_curve, macro),
    }


def calendar_payload(days: int = config.CALENDAR_LOOKAHEAD_DAYS) -> list[MarketEvent]:
    positions = storage.load_portfolio()
    earnings = {
        p.symbol: data.get_next_earnings(p.symbol)
        for p in positions if not p.symbol.endswith(".IS")
    }
    return upcoming_events(date.today(), earnings, days)


def report_payload(symbol: str) -> dict[str, SymbolReport | SymbolContext | str | None]:
    report = build_report(symbol)
    context = build_symbol_context(symbol) if report is not None else None
    commentary = symbol_report_commentary(report, context) if report is not None else None
    return {"report": report, "context": context, "commentary": commentary}


def news_payload(symbol: str, lang: str = "tr") -> list[dict]:
    from . import news

    return news.get_news_for(symbol, lang)


def compare_payload(
    period: str = config.DEFAULT_COMPARE_PERIOD, base: str = "USD"
) -> list[SeriesResult]:
    metrics, cash, usdtry, _histories = _load_metrics()
    all_symbols = tuple(
        dict.fromkeys([*(m.symbol for m in metrics), *config.BENCHMARKS, config.FX_USDTRY])
    )
    histories = data.get_histories(all_symbols, config.COMPARE_HISTORY_PERIOD)
    prices = {m.symbol: histories[m.symbol]["Close"] for m in metrics if m.symbol in histories}
    benchmarks = {sym: histories[sym]["Close"] for sym in config.BENCHMARKS if sym in histories}
    fx_series = (
        histories[config.FX_USDTRY]["Close"]
        if config.FX_USDTRY in histories
        else pd.Series(dtype=float)
    )
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
