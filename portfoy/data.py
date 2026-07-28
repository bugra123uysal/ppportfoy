"""Market data access via yfinance (free, no API key).

Everything is cached with Streamlit's cache and wrapped defensively:
Yahoo endpoints fail or change shape regularly, so every function
degrades to None / empty instead of raising into the UI.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import NamedTuple

import pandas as pd
import streamlit as st
import yfinance as yf

from . import config


class Quote(NamedTuple):
    symbol: str
    price: float
    prev_close: float
    change_pct: float


@st.cache_data(ttl=config.HISTORY_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.QUOTE_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.ROTATION_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.QUOTE_CACHE_TTL, show_spinner=False)
def get_usdtry() -> float | None:
    q = get_quotes((config.FX_USDTRY,)).get(config.FX_USDTRY)
    return q.price if q and q.price > 0 else None


@st.cache_data(ttl=config.QUOTE_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.HISTORY_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.BREADTH_CACHE_TTL, show_spinner=False)
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


@st.cache_data(ttl=config.OPTIONS_CACHE_TTL, show_spinner=False)
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


def symbol_exists(symbol: str) -> bool:
    """Cheap existence check used when the user adds a new position."""
    df = get_history(symbol, period="5d")
    return not df.empty
