"""Stan Weinstein's 4-stage market-cycle analysis, applied to the user's own
portfolio holdings (Evre Takibi) -- not a universe scan, since the whole
point is "where is each of MY positions in its own cycle", not screening for
new ideas.

Weinstein's method (*Secrets for Profiting in Bull and Bear Markets*) reads a
stock's position off its 30-week moving average (~150 trading days) and that
average's own slope:

  Evre 1 (Taban / Basing)    -- price chops sideways around a flattening 30w
                                 MA after a decline. Accumulation; no trend
                                 yet either way.
  Evre 2 (Yükseliş / Advance)-- price breaks above a now-rising 30w MA. The
                                 only stage Weinstein actually wants new long
                                 exposure in.
  Evre 3 (Tepe / Top)        -- the advance stalls, the 30w MA flattens again
                                 after Evre 2, distribution begins.
  Evre 4 (Düşüş / Decline)   -- price breaks below a now-falling 30w MA.
                                 Exit/avoid.

This is a mechanical read of price-vs-SMA and SMA slope -- the same kind of
public, computable signal every other scanner in this app already uses, not
a prediction. The flat-SMA case (Evre 1 vs Evre 3 both look like "price
hugging a flat average") is disambiguated by the SMA's own longer-run slope:
still falling into the flat patch -> coming off a decline -> Evre 1; still
rising into the flat patch -> coming off an advance -> Evre 3.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config
from .indicators import pct_from_52w_high, sma

STAGE_LABELS: dict[int, str] = {
    1: "Evre 1 - Taban Yapıyor",
    2: "Evre 2 - Yükseliş",
    3: "Evre 3 - Tepe / Dağıtım",
    4: "Evre 4 - Düşüş",
}

STAGE_TREND: dict[int, str] = {
    1: "yatay",
    2: "yukselis",
    3: "yatay",
    4: "dusus",
}

# Display order: technical breakdowns (4, 3) surface before basing/advancing
# (1, 2) -- the whole point of a "notify me when something's wrong" view.
STAGE_SEVERITY_RANK: dict[int, int] = {4: 0, 3: 1, 1: 2, 2: 3}

# Weeks of run-length walked back to report "kaç haftadır bu evrede" --
# bounds the classification loop below to a fixed, cheap cost regardless of
# how much history STAGE_ANALYSIS_PERIOD fetched.
_MAX_STAGE_HISTORY_WEEKS = 104


@dataclass(frozen=True)
class StageAnalysis:
    symbol: str
    stage: int                            # 1-4
    stage_label: str
    trend: str                            # "yukselis" | "dusus" | "yatay"
    price: float
    sma30w: float
    sma30w_slope_pct: float
    price_vs_sma_pct: float
    weeks_in_stage: int
    stage_changed: bool                   # this week's stage differs from last week's
    relative_strength_trend: str | None    # "yukselis" | "dusus" | "yatay" | None
    pct_from_52w_high: float | None
    technical_alert: bool                 # Evre 3 or 4 -- teknik bozukluk
    summary_tr: str


def weekly_close(daily_close: pd.Series) -> pd.Series:
    """Resamples a daily close series to weekly bars (Friday-anchored)."""
    if not isinstance(daily_close.index, pd.DatetimeIndex):
        return pd.Series(dtype=float)
    return daily_close.resample("W").last().dropna()


def _direction(slope_pct: float) -> str:
    if slope_pct > config.STAGE_FLAT_THRESHOLD_PCT:
        return "up"
    if slope_pct < -config.STAGE_FLAT_THRESHOLD_PCT:
        return "down"
    return "flat"


def _stage_at(close: pd.Series, sma_line: pd.Series, i: int) -> int | None:
    """Classify the Weinstein stage as of week index `i`, using only data up
    to and including that week. None when there isn't enough history yet to
    judge (not "Evre 1" -- an unknown read must never masquerade as a
    specific one)."""
    lookback = config.STAGE_SLOPE_LOOKBACK_WEEKS
    if i < lookback or pd.isna(sma_line.iloc[i]) or pd.isna(sma_line.iloc[i - lookback]):
        return None

    price = float(close.iloc[i])
    sma_now = float(sma_line.iloc[i])
    sma_prev = float(sma_line.iloc[i - lookback])
    slope_pct = (sma_now / sma_prev - 1.0) * 100.0 if sma_prev else 0.0
    direction = _direction(slope_pct)
    price_above = price > sma_now

    if direction == "up" and price_above:
        return 2
    if direction == "down" and not price_above:
        return 4
    if direction == "flat":
        context = config.STAGE_CONTEXT_LOOKBACK_WEEKS
        j = i - context
        if j < 0 or pd.isna(sma_line.iloc[j]) or sma_line.iloc[j] == 0:
            # No long-run context yet -- fall back to price position alone.
            return 3 if price_above else 1
        context_slope = (sma_now / float(sma_line.iloc[j]) - 1.0) * 100.0
        return 3 if context_slope > 0 else 1
    if direction == "up":  # and not price_above
        return 3   # rising MA but price has dipped under it -- losing Evre 2
    return 1        # direction == "down" and price_above -- testing the base


def _weeks_in_stage(close: pd.Series, sma_line: pd.Series, current_stage: int) -> int:
    last = len(close) - 1
    floor = max(0, last - _MAX_STAGE_HISTORY_WEEKS)
    weeks = 0
    for i in range(last, floor - 1, -1):
        if _stage_at(close, sma_line, i) != current_stage:
            break
        weeks += 1
    return weeks


def _relative_strength_trend(close: pd.Series, benchmark_close: pd.Series | None) -> str | None:
    if benchmark_close is None or benchmark_close.empty:
        return None
    aligned = pd.concat([close, benchmark_close], axis=1, join="inner").dropna()
    lookback = config.STAGE_RS_LOOKBACK_WEEKS
    if len(aligned) < lookback + 1:
        return None
    rs = aligned.iloc[:, 0] / aligned.iloc[:, 1].replace(0.0, np.nan)
    rs = rs.dropna()
    if len(rs) < lookback + 1:
        return None
    now, prev = float(rs.iloc[-1]), float(rs.iloc[-1 - lookback])
    if not prev:
        return None
    change_pct = (now / prev - 1.0) * 100.0
    return {"up": "yukselis", "down": "dusus", "flat": "yatay"}[_direction(change_pct)]


def _summary(symbol: str, stage: int, slope_pct: float, price_vs_sma_pct: float) -> str:
    where = f"ortalamanın {'üstünde' if price_vs_sma_pct >= 0 else 'altında'}"
    if stage == 2:
        return (
            f"{symbol}: Evre 2 (yükseliş) -- 30 haftalık ortalama yükseliyor "
            f"(%{slope_pct:.1f}) ve fiyat {where}."
        )
    if stage == 4:
        return (
            f"{symbol}: Evre 4 (düşüş) -- 30 haftalık ortalama düşüyor "
            f"(%{slope_pct:.1f}) ve fiyat {where}."
        )
    if stage == 3:
        return f"{symbol}: Evre 3 (tepe/dağıtım) -- yükseliş sonrası ortalama yataylaşıyor, {where}"
    return f"{symbol}: Evre 1 (taban) -- düşüş sonrası ortalama yataylaşıyor, {where}"


def classify_symbol(
    symbol: str,
    daily_close: pd.Series,
    benchmark_daily_close: pd.Series | None = None,
) -> StageAnalysis | None:
    """None when there isn't enough weekly history for a real 30-week SMA
    read yet -- Evre Takibi should stay silent on a position rather than
    show a false stage for it (same convention as position_health.py)."""
    close = weekly_close(daily_close)
    if len(close) < config.STAGE_SMA_WEEKS + config.STAGE_SLOPE_LOOKBACK_WEEKS:
        return None

    sma_line = sma(close, config.STAGE_SMA_WEEKS)
    last = len(close) - 1
    stage = _stage_at(close, sma_line, last)
    if stage is None:
        return None

    price = float(close.iloc[last])
    sma_now = float(sma_line.iloc[last])
    sma_prev = float(sma_line.iloc[last - config.STAGE_SLOPE_LOOKBACK_WEEKS])
    slope_pct = (sma_now / sma_prev - 1.0) * 100.0 if sma_prev else 0.0
    price_vs_sma_pct = (price / sma_now - 1.0) * 100.0 if sma_now else 0.0

    weeks_in_stage = _weeks_in_stage(close, sma_line, stage)
    bench_close = weekly_close(benchmark_daily_close) if benchmark_daily_close is not None else None

    return StageAnalysis(
        symbol=symbol,
        stage=stage,
        stage_label=STAGE_LABELS[stage],
        trend=STAGE_TREND[stage],
        price=price,
        sma30w=sma_now,
        sma30w_slope_pct=slope_pct,
        price_vs_sma_pct=price_vs_sma_pct,
        weeks_in_stage=weeks_in_stage,
        stage_changed=weeks_in_stage <= 1,
        relative_strength_trend=_relative_strength_trend(close, bench_close),
        pct_from_52w_high=pct_from_52w_high(daily_close),
        technical_alert=stage in (3, 4),
        summary_tr=_summary(symbol, stage, slope_pct, price_vs_sma_pct),
    )


def build_stage_scan(
    symbols: list[str],
    histories: dict[str, pd.DataFrame],
    benchmark_histories: dict[str, pd.DataFrame],
) -> list[StageAnalysis]:
    """One StageAnalysis per portfolio symbol with enough history, most
    severe (Evre 4) first."""
    out: list[StageAnalysis] = []
    for symbol in symbols:
        df = histories.get(symbol)
        if df is None or df.empty:
            continue
        bench_symbol = config.STAGE_BENCHMARKS.get("TRY" if symbol.endswith(".IS") else "USD")
        bench_df = benchmark_histories.get(bench_symbol) if bench_symbol else None
        result = classify_symbol(
            symbol, df["Close"], bench_df["Close"] if bench_df is not None else None
        )
        if result is not None:
            out.append(result)
    return sorted(out, key=lambda s: (STAGE_SEVERITY_RANK[s.stage], s.symbol))
