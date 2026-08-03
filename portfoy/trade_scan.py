"""My Trade indicator screener -- Group 1/2/3 buy-candidate scan.

Three independent "setups", each a chain of same-direction confirmations
(AND logic within a group, matching how the source notes describe them):

  Group 1: Stochastic Momentum Index gives a buy signal below zero,
           confirmed by volume (above its 20d average + a green candle),
           confirmed again by Bollinger Bands (bounce off the lower band,
           or a break above the mid band).
  Group 2: 21d EMA trend filter (EMA itself rising) + 21d "MAD" (% deviation
           of price from that same EMA) flagging a buy-the-dip pullback
           within the uptrend + 14d Stochastic RSI %K crossing above %D.
  Group 3: An ATR trailing-stop flip to buy (UT Bot -- the public
           substitute the source notes name for their private "BTX"
           indicator) confirmed by a CCI-based trend color (Trend Magic,
           called "KJ MAGIC" in the notes) currently bullish (CCI > 0).

This is a mechanical rule scan over a curated large-cap pool, not backtested
and not investment advice -- thresholds live in config.py.

Pure functions only -- data fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data
from .indicators import (
    atr,
    bollinger_bands,
    cci,
    ema,
    pct_change_last,
    stochastic_momentum_index,
    stochastic_rsi,
    ut_bot_trailing_stop,
    volume_sma,
)


@dataclass(frozen=True)
class TradeSignal:
    symbol: str
    sector: str
    price: float
    change_1d: float
    groups: list[int]              # e.g. [1, 3] -- which groups currently qualify
    atr_14: float | None
    suggested_stop: float | None   # price - atr_14 * config.STOP_ATR_MULT


def _crossed_up(series: pd.Series, other: pd.Series) -> bool:
    """True if `series` closed at/below `other` last bar and above it now."""
    if len(series) < 2 or len(other) < 2:
        return False
    prev_s, prev_o = series.iloc[-2], other.iloc[-2]
    last_s, last_o = series.iloc[-1], other.iloc[-1]
    if any(pd.isna(v) for v in (prev_s, prev_o, last_s, last_o)):
        return False
    return bool(prev_s <= prev_o and last_s > last_o)


def _group1_momentum_volume_bands(df: pd.DataFrame) -> bool:
    smi, signal = stochastic_momentum_index(
        df["High"], df["Low"], df["Close"], config.SMI_PERIOD, config.SMI_SIGNAL, config.SMI_SIGNAL
    )
    if smi.empty or pd.isna(smi.iloc[-1]) or smi.iloc[-1] >= 0:
        return False
    if not _crossed_up(smi, signal):
        return False

    vol_ma = volume_sma(df["Volume"], 20)
    if pd.isna(vol_ma.iloc[-1]):
        return False
    volume_confirm = (
        df["Volume"].iloc[-1] > vol_ma.iloc[-1] and df["Close"].iloc[-1] > df["Open"].iloc[-1]
    )
    if not volume_confirm:
        return False

    upper, mid, lower = bollinger_bands(df["Close"], config.BB_PERIOD, config.BB_STD)
    if pd.isna(lower.iloc[-1]) or pd.isna(mid.iloc[-1]):
        return False
    bb_confirm = df["Close"].iloc[-1] <= lower.iloc[-1] or _crossed_up(df["Close"], mid)
    return bool(bb_confirm)


def _group2_trend_deviation_stochrsi(df: pd.DataFrame) -> bool:
    close = df["Close"]
    ema21 = ema(close, 21)
    if len(ema21) < 6 or ema21.iloc[-6:].isna().any() or ema21.iloc[-1] == 0:
        return False
    trend_up = ema21.iloc[-1] > ema21.iloc[-6]
    if not trend_up:
        return False

    mad_pct = (close.iloc[-1] / ema21.iloc[-1] - 1.0) * 100.0
    if mad_pct > config.MAD_OVERSOLD_PCT:
        return False

    k, d = stochastic_rsi(close, config.STOCH_RSI_PERIOD)
    return _crossed_up(k, d)


def _group3_flip_and_trend(df: pd.DataFrame) -> bool:
    close, high, low = df["Close"], df["High"], df["Low"]
    stop = ut_bot_trailing_stop(close, high, low, config.UT_BOT_KEY_VALUE, config.UT_BOT_ATR_PERIOD)
    if not _crossed_up(close, stop):
        return False

    cci_values = cci(high, low, close, config.TREND_MAGIC_CCI_PERIOD)
    if pd.isna(cci_values.iloc[-1]):
        return False
    return bool(cci_values.iloc[-1] > 0)


def build_trade_scan(universe: dict[str, str]) -> list[TradeSignal]:
    """Scan `universe` (ticker -> sector label) and group matches by setup."""
    results: list[TradeSignal] = []
    for symbol, sector in universe.items():
        df = data.get_history(symbol, period=config.TRADE_SCAN_HISTORY_PERIOD)
        if df.empty or len(df) < config.BB_PERIOD + config.SMI_SIGNAL * 2:
            continue

        groups: list[int] = []
        if _group1_momentum_volume_bands(df):
            groups.append(1)
        if _group2_trend_deviation_stochrsi(df):
            groups.append(2)
        if _group3_flip_and_trend(df):
            groups.append(3)
        if not groups:
            continue

        price = float(df["Close"].iloc[-1])
        atr14 = atr(df["High"], df["Low"], df["Close"], 14)
        atr_last = None if atr14.empty or pd.isna(atr14.iloc[-1]) else float(atr14.iloc[-1])
        suggested_stop = (
            round(price - atr_last * config.STOP_ATR_MULT, 2) if atr_last is not None else None
        )
        results.append(
            TradeSignal(
                symbol=symbol,
                sector=sector,
                price=price,
                change_1d=pct_change_last(df["Close"]),
                groups=groups,
                atr_14=atr_last,
                suggested_stop=suggested_stop,
            )
        )
    return results
