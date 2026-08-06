"""My Trade indicator screener -- Group 1-4, each usable long or short.

Four independent "setups" (source: user-provided course notes, see the
per-group breakdown below). Each setup is a chain of same-direction
confirmations (AND logic within a group), and each is bidirectional: the
source notes describe a bullish ("Al"/buy) reading and, for most groups, an
explicit bearish ("Sat"/sell) mirror reading of the same indicators --  not
a separate setup. `groups: list[int]` on a `TradeSignal` records which of
these four setups matched; `direction` records which side (long/short) they
matched on.

  Group 1: Stochastic Momentum Index gives a buy signal below zero (sell
           signal above zero, mirrored -- see the note on that function),
           confirmed by volume (above its 20d average + a green/red
           candle), confirmed again by Bollinger Bands (bounce off the
           lower/upper band, or a break through the mid band).
  Group 2: 21d EMA trend filter (EMA itself rising/falling) + 21d "MAD" (%
           deviation of price from that same EMA) explicitly flags both a
           buy-the-dip pullback in an uptrend ("aşırı ucuz", green) and an
           overbought rally in a downtrend ("aşırı şişkin", red) + 14d
           Stochastic RSI %K crossing above/below %D.
  Group 3: An ATR trailing-stop flip (UT Bot -- the public substitute the
           source notes name for their private "BTX"/"B't X" indicator)
           confirmed by a CCI-based trend color (Trend Magic, called
           "KJ MAGIC" in the notes) -- explicitly bidirectional in the
           notes (mavi/blue = buy, kırmızı/red = sell).
  Group 4: A 14d Stochastic RSI %K crossing its own added 14d EMA (the
           notes describe adding "an EMA strategy" on top of the existing
           Stochastic RSI), confirmed -- on the buy side only, per the
           notes -- by TradingView's built-in "Median" indicator (rolling
           median of hl2 vs its own EMA, same length) reading bullish
           ("Medyan yeşil"). The notes only condition the buy side on the
           Median color; the sell side is stated as the bare EMA-cross
           ("RSI hareketli ortalamanın altına geçtiyse satış"), so that
           asymmetry (buy needs 2 confirmations, sell needs 1) is
           intentional here, not an oversight.

Group 1's sell/short mirror has no explicit description in the source
notes (unlike 2/3/4, which the notes state are bidirectional) -- it's this
codebase's own systematic extension, by the same logic a screener normally
turns a long setup into a short one (flip every comparison). Flagged here
because it's the one group whose short side isn't source-verified.

Stocks don't only go up: a short/açığa satış signal here is still just a
mechanical entry trigger, not a green light to short. Actually opening a
short (unlike going long) needs a margin account with short-selling
enabled and locate/borrow availability, carries margin/borrow-fee costs
that accrue while the position is open, and has theoretically unlimited
risk (the stock can rise indefinitely, unlike a long which floors at
zero) -- check your broker's short-squeeze/borrow-fee exposure before
acting on any sell-side match. Options (puts) or inverse ETFs are a
capped-risk alternative to an outright short.

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
    median_price,
    pct_change_last,
    pct_from_52w_high,
    pct_from_52w_low,
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
    direction: str                 # "long" | "short"
    groups: list[int]              # e.g. [1, 3] -- which of Group 1-4 currently qualify
    atr_14: float | None
    suggested_stop: float | None   # long: price - atr_14*mult; short: price + atr_14*mult
    pct_from_52w_high: float | None    # <=0; 0 = sitting at the 52-week high
    pct_from_52w_low: float | None     # >=0; 0 = sitting at the 52-week low
    weekly_trend_aligned: bool | None  # weekly EMA agrees with direction; None = not enough history


def _crossed_up(series: pd.Series, other: pd.Series) -> bool:
    """True if `series` closed at/below `other` last bar and above it now."""
    if len(series) < 2 or len(other) < 2:
        return False
    prev_s, prev_o = series.iloc[-2], other.iloc[-2]
    last_s, last_o = series.iloc[-1], other.iloc[-1]
    if any(pd.isna(v) for v in (prev_s, prev_o, last_s, last_o)):
        return False
    return bool(prev_s <= prev_o and last_s > last_o)


def _crossed_down(series: pd.Series, other: pd.Series) -> bool:
    """True if `series` closed at/above `other` last bar and below it now."""
    if len(series) < 2 or len(other) < 2:
        return False
    prev_s, prev_o = series.iloc[-2], other.iloc[-2]
    last_s, last_o = series.iloc[-1], other.iloc[-1]
    if any(pd.isna(v) for v in (prev_s, prev_o, last_s, last_o)):
        return False
    return bool(prev_s >= prev_o and last_s < last_o)


def _group1_buy_momentum_volume_bands(df: pd.DataFrame) -> bool:
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


def _group1_sell_momentum_volume_bands(df: pd.DataFrame) -> bool:
    """This codebase's own bearish mirror of Group 1 -- see module docstring."""
    smi, signal = stochastic_momentum_index(
        df["High"], df["Low"], df["Close"], config.SMI_PERIOD, config.SMI_SIGNAL, config.SMI_SIGNAL
    )
    if smi.empty or pd.isna(smi.iloc[-1]) or smi.iloc[-1] <= 0:
        return False
    if not _crossed_down(smi, signal):
        return False

    vol_ma = volume_sma(df["Volume"], 20)
    if pd.isna(vol_ma.iloc[-1]):
        return False
    volume_confirm = (
        df["Volume"].iloc[-1] > vol_ma.iloc[-1] and df["Close"].iloc[-1] < df["Open"].iloc[-1]
    )
    if not volume_confirm:
        return False

    upper, mid, lower = bollinger_bands(df["Close"], config.BB_PERIOD, config.BB_STD)
    if pd.isna(upper.iloc[-1]) or pd.isna(mid.iloc[-1]):
        return False
    bb_confirm = df["Close"].iloc[-1] >= upper.iloc[-1] or _crossed_down(df["Close"], mid)
    return bool(bb_confirm)


def _group2_buy_trend_deviation_stochrsi(df: pd.DataFrame) -> bool:
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


def _group2_sell_trend_deviation_stochrsi(df: pd.DataFrame) -> bool:
    close = df["Close"]
    ema21 = ema(close, 21)
    if len(ema21) < 6 or ema21.iloc[-6:].isna().any() or ema21.iloc[-1] == 0:
        return False
    trend_down = ema21.iloc[-1] < ema21.iloc[-6]
    if not trend_down:
        return False

    mad_pct = (close.iloc[-1] / ema21.iloc[-1] - 1.0) * 100.0
    if mad_pct < config.MAD_OVERBOUGHT_PCT:
        return False

    k, d = stochastic_rsi(close, config.STOCH_RSI_PERIOD)
    return _crossed_down(k, d)


def _group3_buy_flip_and_trend(df: pd.DataFrame) -> bool:
    close, high, low = df["Close"], df["High"], df["Low"]
    stop = ut_bot_trailing_stop(close, high, low, config.UT_BOT_KEY_VALUE, config.UT_BOT_ATR_PERIOD)
    if not _crossed_up(close, stop):
        return False

    cci_values = cci(high, low, close, config.TREND_MAGIC_CCI_PERIOD)
    if pd.isna(cci_values.iloc[-1]):
        return False
    return bool(cci_values.iloc[-1] > 0)


def _group3_sell_flip_and_trend(df: pd.DataFrame) -> bool:
    close, high, low = df["Close"], df["High"], df["Low"]
    stop = ut_bot_trailing_stop(close, high, low, config.UT_BOT_KEY_VALUE, config.UT_BOT_ATR_PERIOD)
    if not _crossed_down(close, stop):
        return False

    cci_values = cci(high, low, close, config.TREND_MAGIC_CCI_PERIOD)
    if pd.isna(cci_values.iloc[-1]):
        return False
    return bool(cci_values.iloc[-1] < 0)


def _median_trend_up(df: pd.DataFrame) -> bool | None:
    """True/False for Median-vs-its-EMA color, None if not enough history yet."""
    median = median_price(df["High"], df["Low"], config.MEDIAN_PERIOD)
    median_ema = ema(median, config.MEDIAN_PERIOD)
    if median.empty or pd.isna(median.iloc[-1]) or pd.isna(median_ema.iloc[-1]):
        return None
    return bool(median.iloc[-1] > median_ema.iloc[-1])


def _group4_buy_stochrsi_ema_median(df: pd.DataFrame) -> bool:
    median_up = _median_trend_up(df)
    if not median_up:
        return False

    k, _d = stochastic_rsi(df["Close"], config.STOCH_RSI_PERIOD)
    k_ema = ema(k, config.GROUP4_RSI_EMA_PERIOD)
    return _crossed_up(k, k_ema)


def _group4_sell_stochrsi_ema(df: pd.DataFrame) -> bool:
    """No Median confirmation on the sell side -- see module docstring."""
    k, _d = stochastic_rsi(df["Close"], config.STOCH_RSI_PERIOD)
    k_ema = ema(k, config.GROUP4_RSI_EMA_PERIOD)
    return _crossed_down(k, k_ema)


def _atr_last(df: pd.DataFrame) -> float | None:
    atr14 = atr(df["High"], df["Low"], df["Close"], 14)
    return None if atr14.empty or pd.isna(atr14.iloc[-1]) else float(atr14.iloc[-1])


def _weekly_trend_up(df: pd.DataFrame) -> bool | None:
    """Weekly EMA direction, resampled from the same daily frame already
    fetched for the daily setups -- no extra network call. None means not
    enough weekly history yet to judge, not "flat"."""
    if not isinstance(df.index, pd.DatetimeIndex):
        return None
    weekly = df["Close"].resample("W").last().dropna()
    period = config.WEEKLY_TREND_EMA
    if len(weekly) < period + 6:
        return None
    weekly_ema = ema(weekly, period)
    if weekly_ema.iloc[-6:].isna().any():
        return None
    return bool(weekly_ema.iloc[-1] > weekly_ema.iloc[-6])


def build_trade_scan(universe: dict[str, str]) -> list[TradeSignal]:
    """Scan `universe` (ticker -> sector label) and group matches by setup.

    A symbol can independently qualify long, short, or (the four setups
    check different indicators) both at once; each direction that matches
    becomes its own `TradeSignal` so the suggested stop is never ambiguous
    about which side of price it sits on.
    """
    histories = data.get_histories(tuple(universe), period=config.TRADE_SCAN_HISTORY_PERIOD)
    results: list[TradeSignal] = []
    for symbol, sector in universe.items():
        df = histories.get(symbol, pd.DataFrame())
        if df.empty or len(df) < config.BB_PERIOD + config.SMI_SIGNAL * 2:
            continue

        long_groups: list[int] = []
        if _group1_buy_momentum_volume_bands(df):
            long_groups.append(1)
        if _group2_buy_trend_deviation_stochrsi(df):
            long_groups.append(2)
        if _group3_buy_flip_and_trend(df):
            long_groups.append(3)
        if _group4_buy_stochrsi_ema_median(df):
            long_groups.append(4)

        short_groups: list[int] = []
        if _group1_sell_momentum_volume_bands(df):
            short_groups.append(1)
        if _group2_sell_trend_deviation_stochrsi(df):
            short_groups.append(2)
        if _group3_sell_flip_and_trend(df):
            short_groups.append(3)
        if _group4_sell_stochrsi_ema(df):
            short_groups.append(4)

        if not long_groups and not short_groups:
            continue

        price = float(df["Close"].iloc[-1])
        atr_last = _atr_last(df)
        change_1d = pct_change_last(df["Close"])
        high52 = pct_from_52w_high(df["Close"], config.WEEK_52_TRADING_DAYS)
        low52 = pct_from_52w_low(df["Close"], config.WEEK_52_TRADING_DAYS)
        weekly_up = _weekly_trend_up(df)

        if long_groups:
            suggested_stop = (
                round(price - atr_last * config.STOP_ATR_MULT, 2) if atr_last is not None else None
            )
            results.append(
                TradeSignal(
                    symbol=symbol,
                    sector=sector,
                    price=price,
                    change_1d=change_1d,
                    direction="long",
                    groups=long_groups,
                    atr_14=atr_last,
                    suggested_stop=suggested_stop,
                    pct_from_52w_high=high52,
                    pct_from_52w_low=low52,
                    weekly_trend_aligned=weekly_up,
                )
            )
        if short_groups:
            suggested_stop = (
                round(price + atr_last * config.STOP_ATR_MULT, 2) if atr_last is not None else None
            )
            results.append(
                TradeSignal(
                    symbol=symbol,
                    sector=sector,
                    price=price,
                    change_1d=change_1d,
                    direction="short",
                    groups=short_groups,
                    atr_14=atr_last,
                    suggested_stop=suggested_stop,
                    pct_from_52w_high=high52,
                    pct_from_52w_low=low52,
                    weekly_trend_aligned=(None if weekly_up is None else not weekly_up),
                )
            )
    return results
