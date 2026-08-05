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


def ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, min_periods=period, adjust=False).mean()


def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
    return sma(volume, period)


def median_price(high: pd.Series, low: pd.Series, period: int = 3) -> pd.Series:
    """TradingView's built-in "Median" indicator's core line: the rolling
    statistical median (not a moving average) of hl2 over `period` bars.
    Its ATR-based envelope bands are a pure display feature (the source
    notes explicitly hide them) and carry no signal, so they're not
    modeled here -- only this line, compared against its own EMA by the
    caller, is used.
    """
    hl2 = (high + low) / 2.0
    return hl2.rolling(window=period, min_periods=period).median()


def bollinger_bands(
    close: pd.Series, period: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Upper, mid (SMA), lower bands."""
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    return mid + num_std * std, mid, mid - num_std * std


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Commodity Channel Index."""
    typical = (high + low + close) / 3.0
    mean_dev = typical.rolling(window=period, min_periods=period).apply(
        lambda window: np.abs(window - window.mean()).mean(), raw=True
    )
    return (typical - sma(typical, period)) / (0.015 * mean_dev.replace(0.0, np.nan))


def stochastic_momentum_index(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 10,
    d_period: int = 3,
    signal_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """SMI and its EMA signal line. Range approx +100..-100."""
    hh = high.rolling(window=k_period, min_periods=k_period).max()
    ll = low.rolling(window=k_period, min_periods=k_period).min()
    midpoint_dist = close - (hh + ll) / 2.0
    hl_range = hh - ll
    smoothed_dist = midpoint_dist.ewm(span=d_period, min_periods=d_period, adjust=False).mean()
    smoothed_dist = smoothed_dist.ewm(span=d_period, min_periods=d_period, adjust=False).mean()
    smoothed_range = hl_range.ewm(span=d_period, min_periods=d_period, adjust=False).mean()
    smoothed_range = smoothed_range.ewm(span=d_period, min_periods=d_period, adjust=False).mean()
    smi = 100.0 * (smoothed_dist / (smoothed_range / 2.0).replace(0.0, np.nan))
    signal = smi.ewm(span=signal_period, min_periods=signal_period, adjust=False).mean()
    return smi, signal


def stochastic_rsi(
    close: pd.Series,
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_smooth: int = 3,
    d_smooth: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """%K and %D of the Stochastic RSI, 0..100 scale."""
    rsi_values = rsi(close, rsi_period)
    lowest = rsi_values.rolling(window=stoch_period, min_periods=stoch_period).min()
    highest = rsi_values.rolling(window=stoch_period, min_periods=stoch_period).max()
    raw_k = 100.0 * (rsi_values - lowest) / (highest - lowest).replace(0.0, np.nan)
    k = raw_k.rolling(window=k_smooth, min_periods=k_smooth).mean()
    d = k.rolling(window=d_smooth, min_periods=d_smooth).mean()
    return k, d


def chaikin_money_flow(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20
) -> pd.Series:
    """Chaikin Money Flow. Positive = accumulation, negative = distribution."""
    hl_range = (high - low).replace(0.0, np.nan)
    money_flow_multiplier = ((close - low) - (high - close)) / hl_range
    money_flow_volume = money_flow_multiplier * volume
    return (
        money_flow_volume.rolling(window=period, min_periods=period).sum()
        / volume.rolling(window=period, min_periods=period).sum().replace(0.0, np.nan)
    )


def money_flow_index(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14
) -> pd.Series:
    """Volume-weighted RSI. 0..100 scale."""
    typical = (high + low + close) / 3.0
    raw_money_flow = typical * volume
    rises = typical.diff() > 0
    positive_flow = raw_money_flow.where(rises, 0.0)
    negative_flow = raw_money_flow.where(~rises, 0.0)
    positive_sum = positive_flow.rolling(window=period, min_periods=period).sum()
    negative_sum = negative_flow.rolling(window=period, min_periods=period).sum()
    money_ratio = positive_sum / negative_sum.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + money_ratio)
    return out.fillna(100.0).where(negative_sum.notna(), np.nan)


def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Cumulative volume, signed by the day's price direction."""
    direction = np.sign(close.diff().fillna(0.0))
    return (direction * volume).cumsum()


def ut_bot_trailing_stop(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    key_value: float = 2.0,
    atr_period: int = 10,
) -> pd.Series:
    """ATR trailing-stop line (UT Bot). A fresh close above it flips to buy."""
    atr_values = atr(high, low, close, atr_period) * key_value
    stop = pd.Series(np.nan, index=close.index)
    for i in range(len(close)):
        if i == 0 or pd.isna(atr_values.iloc[i]):
            continue
        price, dist, prev_stop = close.iloc[i], atr_values.iloc[i], stop.iloc[i - 1]
        if pd.isna(prev_stop):
            stop.iloc[i] = price - dist
            continue
        prev_price = close.iloc[i - 1]
        if price > prev_stop and prev_price > prev_stop:
            stop.iloc[i] = max(prev_stop, price - dist)
        elif price < prev_stop and prev_price < prev_stop:
            stop.iloc[i] = min(prev_stop, price + dist)
        elif price > prev_stop:
            stop.iloc[i] = price - dist
        else:
            stop.iloc[i] = price + dist
    return stop
