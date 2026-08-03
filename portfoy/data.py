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


def symbol_exists(symbol: str) -> bool:
    """Cheap existence check used when the user adds a new position."""
    df = get_history(symbol, period="5d")
    return not df.empty
