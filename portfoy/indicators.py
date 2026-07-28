"""Pure technical-indicator math on pandas Series/DataFrames. No I/O here."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(window=period, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(100.0).where(avg_loss.notna(), np.nan)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder smoothing)."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def pct_change_last(close: pd.Series) -> float:
    """Last close vs previous close, in percent. NaN-safe."""
    clean = close.dropna()
    if len(clean) < 2:
        return 0.0
    prev, last = float(clean.iloc[-2]), float(clean.iloc[-1])
    if prev == 0:
        return 0.0
    return (last / prev - 1.0) * 100.0


def drawdown_from_peak(close: pd.Series) -> float:
    """Current % distance from the highest close in the series (<= 0)."""
    clean = close.dropna()
    if clean.empty:
        return 0.0
    peak = float(clean.max())
    if peak <= 0:
        return 0.0
    return (float(clean.iloc[-1]) / peak - 1.0) * 100.0


def last_value(series: pd.Series) -> float | None:
    clean = series.dropna()
    if clean.empty:
        return None
    return float(clean.iloc[-1])
