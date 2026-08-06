"""Market data access via yfinance (free, no API key).

Everything is cached (see portfoy.cache -- in-process for local dev/tests,
Upstash Redis for the Vercel API) and wrapped defensively: Yahoo endpoints
fail or change shape regularly, so every function degrades to None / empty
instead of raising into the caller.
"""

from __future__ import annotations

import io
import json
from datetime import date, datetime, timedelta
from typing import NamedTuple

import pandas as pd
import yfinance as yf

from . import config
from .cache import cached
from .serialize import to_jsonable


class Quote(NamedTuple):
    symbol: str
    price: float
    prev_close: float
    change_pct: float


def _encode_price_frame(df: pd.DataFrame) -> str:
    return df.to_json(orient="split", date_format="iso")


def _decode_price_frame(raw: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(raw), orient="split")
    df.index = pd.to_datetime(df.index)
    return df


def _encode_quotes(quotes: dict[str, Quote]) -> str:
    return json.dumps({sym: list(q) for sym, q in quotes.items()})


def _decode_quotes(raw: str) -> dict[str, Quote]:
    return {sym: Quote(*values) for sym, values in json.loads(raw).items()}


def _encode_date(value: date | None) -> str:
    return value.isoformat() if value else ""


def _decode_date(raw: str) -> date | None:
    return date.fromisoformat(raw) if raw else None


def _encode_activity(activity: object) -> str:
    return "" if activity is None else json.dumps(to_jsonable(activity))


def _decode_activity(raw: str):
    if not raw:
        return None
    from .options import OptionActivity

    return OptionActivity(**json.loads(raw))


@cached(ttl=config.HISTORY_CACHE_TTL, encode=_encode_price_frame, decode=_decode_price_frame)
def get_history(symbol: str, period: str = config.DEFAULT_HISTORY_PERIOD) -> pd.DataFrame:
    """Daily OHLCV history. Empty DataFrame on any failure."""
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    needed = {"Open", "High", "Low", "Close"}
    if not needed.issubset(df.columns):
        return pd.DataFrame()
    return df.dropna(subset=["Close"])


def _encode_price_frames(frames: dict[str, pd.DataFrame]) -> str:
    return json.dumps({sym: _encode_price_frame(df) for sym, df in frames.items()})


def _decode_price_frames(raw: str) -> dict[str, pd.DataFrame]:
    return {sym: _decode_price_frame(blob) for sym, blob in json.loads(raw).items()}


@cached(ttl=config.HISTORY_CACHE_TTL, encode=_encode_price_frames, decode=_decode_price_frames)
def get_histories(
    symbols: tuple[str, ...], period: str = config.DEFAULT_HISTORY_PERIOD
) -> dict[str, pd.DataFrame]:
    """Daily OHLCV history for many symbols in one batched request.

    Same shape as N calls to `get_history`, but one network round trip
    (yfinance's own thread pool) instead of N sequential ones -- the
    difference between a page load that waits on one slow request and one
    that waits on `len(symbols)` of them. Symbols that fail or come back
    empty are simply absent from the result, same as `get_history` returning
    an empty frame for a single symbol.
    """
    if not symbols:
        return {}
    try:
        df = yf.download(
            list(symbols), period=period, interval="1d",
            auto_adjust=True, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return {}
    if df is None or df.empty:
        return {}
    needed = {"Open", "High", "Low", "Close"}
    out: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        try:
            sub = df[sym] if isinstance(df.columns, pd.MultiIndex) else df
            if not needed.issubset(sub.columns):
                continue
            sub = sub.dropna(subset=["Close"])
            if not sub.empty:
                out[sym] = sub
        except (KeyError, TypeError):
            continue
    return out


@cached(ttl=config.QUOTE_CACHE_TTL, encode=_encode_quotes, decode=_decode_quotes)
def get_quotes(symbols: tuple[str, ...]) -> dict[str, Quote]:
    """Batch quotes derived from 5 days of closes (robust across yf versions)."""
    if not symbols:
        return {}
    try:
        df = yf.download(
            list(symbols), period="5d", interval="1d",
            auto_adjust=True, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return {}
    if df is None or df.empty:
        return {}
    quotes: dict[str, Quote] = {}
    for sym in symbols:
        try:
            closes = (df[sym]["Close"] if isinstance(df.columns, pd.MultiIndex)
                      else df["Close"]).dropna()
            if closes.empty:
                continue
            price = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) > 1 else price
            change = (price / prev - 1.0) * 100.0 if prev else 0.0
            quotes[sym] = Quote(sym, price, prev, change)
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return quotes


@cached(ttl=config.ROTATION_CACHE_TTL, encode=_encode_price_frame, decode=_decode_price_frame)
def get_weekly_closes(symbols: tuple[str, ...], period: str = config.RRG_PERIOD) -> pd.DataFrame:
    """Weekly closing prices for several symbols, one column per symbol."""
    if not symbols:
        return pd.DataFrame()
    try:
        df = yf.download(
            list(symbols), period=period, interval="1wk",
            auto_adjust=True, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    columns: dict[str, pd.Series] = {}
    for sym in symbols:
        try:
            closes = (df[sym]["Close"] if isinstance(df.columns, pd.MultiIndex)
                      else df["Close"]).dropna()
            if not closes.empty:
                columns[sym] = closes
        except (KeyError, IndexError, TypeError):
            continue
    return pd.DataFrame(columns) if columns else pd.DataFrame()


@cached(ttl=config.QUOTE_CACHE_TTL)
def get_usdtry() -> float | None:
    q = get_quotes((config.FX_USDTRY,)).get(config.FX_USDTRY)
    return q.price if q and q.price > 0 else None


@cached(ttl=config.QUOTE_CACHE_TTL)
def get_macro_snapshot() -> list[dict]:
    """Quotes for the macro strip, in config order."""
    quotes = get_quotes(tuple(config.MACRO_TICKERS))
    out = []
    for sym, label in config.MACRO_TICKERS.items():
        q = quotes.get(sym)
        if q:
            out.append({"symbol": sym, "label": label,
                        "price": q.price, "change_pct": q.change_pct})
    return out


@cached(ttl=config.HISTORY_CACHE_TTL, encode=_encode_date, decode=_decode_date)
def get_next_earnings(symbol: str) -> date | None:
    """Next earnings date if Yahoo exposes one. None otherwise."""
    try:
        cal = yf.Ticker(symbol).calendar
    except Exception:
        return None
    dates = None
    if isinstance(cal, dict):
        dates = cal.get("Earnings Date")
    elif isinstance(cal, pd.DataFrame) and "Earnings Date" in getattr(cal, "index", []):
        dates = list(cal.loc["Earnings Date"])
    if not dates:
        return None
    first = dates[0] if isinstance(dates, (list, tuple)) else dates
    if isinstance(first, datetime):
        first = first.date()
    if isinstance(first, date) and date.today() <= first <= date.today() + timedelta(days=120):
        return first
    return None


@cached(ttl=config.BREADTH_CACHE_TTL, encode=_encode_price_frame, decode=_decode_price_frame)
def get_daily_closes(symbols: tuple[str, ...], period: str = "1y") -> pd.DataFrame:
    """Daily closes for many symbols, one column per symbol (breadth input)."""
    if not symbols:
        return pd.DataFrame()
    try:
        df = yf.download(
            list(symbols), period=period, interval="1d",
            auto_adjust=True, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    columns: dict[str, pd.Series] = {}
    for sym in symbols:
        try:
            closes = (df[sym]["Close"] if isinstance(df.columns, pd.MultiIndex)
                      else df["Close"]).dropna()
            if not closes.empty:
                columns[sym] = closes
        except (KeyError, IndexError, TypeError):
            continue
    return pd.DataFrame(columns) if columns else pd.DataFrame()


@cached(ttl=config.BREADTH_CACHE_TTL, encode=_encode_price_frame, decode=_decode_price_frame)
def get_daily_volumes(symbols: tuple[str, ...], period: str = "1y") -> pd.DataFrame:
    """Daily volume for many symbols, one column per symbol (TRIN input)."""
    if not symbols:
        return pd.DataFrame()
    try:
        df = yf.download(
            list(symbols), period=period, interval="1d",
            auto_adjust=True, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    columns: dict[str, pd.Series] = {}
    for sym in symbols:
        try:
            volume = (df[sym]["Volume"] if isinstance(df.columns, pd.MultiIndex)
                      else df["Volume"]).dropna()
            if not volume.empty:
                columns[sym] = volume
        except (KeyError, IndexError, TypeError):
            continue
    return pd.DataFrame(columns) if columns else pd.DataFrame()


@cached(ttl=config.OPTIONS_CACHE_TTL, encode=_encode_activity, decode=_decode_activity)
def get_option_activity(symbol: str):
    """Aggregated option activity for the nearest expiry. None when no chain."""
    from .options import aggregate_chain, build_activity

    try:
        ticker = yf.Ticker(symbol)
        expiries = ticker.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = ticker.option_chain(expiry)
    except Exception:
        return None
    try:
        summary = aggregate_chain(chain.calls, chain.puts)
    except (AttributeError, KeyError, TypeError):
        return None
    return build_activity(symbol, str(expiry), summary)


class OwnershipFlow(NamedTuple):
    institutional_pct: float | None    # % of shares held by institutions
    insider_net_pct_6m: float | None   # net insider buying (+) / selling (-) as % of shares held


def _encode_ownership(flow: OwnershipFlow | None) -> str:
    return "" if flow is None else json.dumps(list(flow))


def _decode_ownership(raw: str) -> OwnershipFlow | None:
    return None if not raw else OwnershipFlow(*json.loads(raw))


@cached(ttl=config.OWNERSHIP_CACHE_TTL, encode=_encode_ownership, decode=_decode_ownership)
def get_ownership_flow(symbol: str) -> OwnershipFlow | None:
    """Institutional ownership % and 6-month net insider buying (Yahoo Holders tab)."""
    try:
        ticker = yf.Ticker(symbol)
        major = ticker.major_holders
        purchases = ticker.insider_purchases
    except Exception:
        return None

    institutional_pct = None
    if major is not None and not major.empty and "institutionsPercentHeld" in major.index:
        try:
            institutional_pct = float(major.loc["institutionsPercentHeld", "Value"]) * 100.0
        except (KeyError, TypeError, ValueError):
            institutional_pct = None

    insider_net_pct_6m = None
    if purchases is not None and not purchases.empty:
        label_col = "Insider Purchases Last 6m"
        row = purchases[purchases[label_col] == "% Net Shares Purchased (Sold)"]
        if not row.empty:
            try:
                insider_net_pct_6m = float(row["Shares"].iloc[0]) * 100.0
            except (TypeError, ValueError):
                insider_net_pct_6m = None

    if institutional_pct is None and insider_net_pct_6m is None:
        return None
    return OwnershipFlow(institutional_pct, insider_net_pct_6m)


class AnalystView(NamedTuple):
    target_mean: float | None
    target_high: float | None
    target_low: float | None
    consensus: str | None      # "al" | "tut" | "sat" -- majority of current-month ratings
    num_analysts: int | None


def _encode_analyst(view: AnalystView | None) -> str:
    return "" if view is None else json.dumps(list(view))


def _decode_analyst(raw: str) -> AnalystView | None:
    return None if not raw else AnalystView(*json.loads(raw))


def _fetch_price_targets(ticker: yf.Ticker) -> tuple[float | None, float | None, float | None]:
    try:
        targets = ticker.analyst_price_targets
    except Exception:
        return None, None, None
    if not targets:
        return None, None, None
    return (
        _to_optional_float(targets.get("mean")),
        _to_optional_float(targets.get("high")),
        _to_optional_float(targets.get("low")),
    )


def _fetch_consensus(ticker: yf.Ticker) -> tuple[str | None, int | None]:
    """Majority bucket (al/tut/sat) of the current-month analyst rating counts."""
    try:
        summary = ticker.recommendations_summary
    except Exception:
        return None, None
    if summary is None or summary.empty:
        return None, None
    row = summary[summary["period"] == "0m"]
    if row.empty:
        return None, None
    r = row.iloc[0]
    buy = int(r.get("strongBuy", 0)) + int(r.get("buy", 0))
    hold = int(r.get("hold", 0))
    sell = int(r.get("sell", 0)) + int(r.get("strongSell", 0))
    total = buy + hold + sell
    if total == 0:
        return None, None
    buckets = (("al", buy), ("tut", hold), ("sat", sell))
    return max(buckets, key=lambda kv: kv[1])[0], total


@cached(ttl=config.OWNERSHIP_CACHE_TTL, encode=_encode_analyst, decode=_decode_analyst)
def get_analyst_view(symbol: str) -> AnalystView | None:
    """Analyst price targets + current-month buy/hold/sell consensus (Yahoo, free).

    Two independent Yahoo reads, both allowed to fail on their own: a stock
    can have price targets without a fresh ratings breakdown, or vice versa.
    """
    try:
        ticker = yf.Ticker(symbol)
    except Exception:
        return None

    target_mean, target_high, target_low = _fetch_price_targets(ticker)
    consensus, num_analysts = _fetch_consensus(ticker)

    if target_mean is None and consensus is None:
        return None
    return AnalystView(target_mean, target_high, target_low, consensus, num_analysts)


def _to_optional_float(value: object) -> float | None:
    try:
        return None if value is None else float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class FundamentalMetrics(NamedTuple):
    pe: float | None
    peg: float | None                  # derived: trailing P/E / (earnings growth * 100)
    ev_ebitda: float | None
    revenue_growth: float | None       # % YoY
    gross_margin: float | None         # %
    operating_margin: float | None     # %
    roe: float | None                  # %
    debt_to_equity: float | None
    fcf_yield: float | None            # % of market cap


def _encode_fundamentals(m: FundamentalMetrics | None) -> str:
    return "" if m is None else json.dumps(list(m))


def _decode_fundamentals(raw: str) -> FundamentalMetrics | None:
    return None if not raw else FundamentalMetrics(*json.loads(raw))


@cached(ttl=config.FUNDAMENTALS_CACHE_TTL, encode=_encode_fundamentals, decode=_decode_fundamentals)
def get_fundamentals(symbol: str) -> FundamentalMetrics | None:
    """Valuation/quality/growth metrics from Yahoo's quote summary (free,
    the same data `Ticker.info` already wraps -- no separate paid endpoint).

    PEG isn't read directly: Yahoo dropped a reliable `pegRatio` field, so
    it's derived from trailing P/E and forward earnings growth instead, which
    is the same arithmetic PEG has always been (P/E ÷ expected growth rate).
    """
    try:
        info = yf.Ticker(symbol).info
    except Exception:
        return None
    if not info:
        return None

    pe = _to_optional_float(info.get("trailingPE"))
    ev_ebitda = _to_optional_float(info.get("enterpriseToEbitda"))
    revenue_growth = _to_optional_float(info.get("revenueGrowth"))
    earnings_growth = _to_optional_float(info.get("earningsGrowth"))
    gross_margin = _to_optional_float(info.get("grossMargins"))
    operating_margin = _to_optional_float(info.get("operatingMargins"))
    roe = _to_optional_float(info.get("returnOnEquity"))
    debt_to_equity = _to_optional_float(info.get("debtToEquity"))
    fcf = _to_optional_float(info.get("freeCashflow"))
    market_cap = _to_optional_float(info.get("marketCap"))

    if pe is None and ev_ebitda is None and revenue_growth is None:
        return None

    peg = (
        pe / (earnings_growth * 100.0)
        if pe is not None and earnings_growth is not None and earnings_growth > 0
        else None
    )
    fcf_yield = (
        (fcf / market_cap) * 100.0 if fcf is not None and market_cap is not None and market_cap > 0
        else None
    )

    return FundamentalMetrics(
        pe=pe,
        peg=peg,
        ev_ebitda=ev_ebitda,
        revenue_growth=None if revenue_growth is None else revenue_growth * 100.0,
        gross_margin=None if gross_margin is None else gross_margin * 100.0,
        operating_margin=None if operating_margin is None else operating_margin * 100.0,
        roe=None if roe is None else roe * 100.0,
        debt_to_equity=debt_to_equity,
        fcf_yield=fcf_yield,
    )


def symbol_exists(symbol: str) -> bool:
    """Cheap existence check used when the user adds a new position."""
    df = get_history(symbol, period="5d")
    return not df.empty
