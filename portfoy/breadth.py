"""Market breadth (internals) maths — how many stocks join the trend.

An index can climb while most of its members fall (a few mega-caps doing
the lifting). Breadth exposes that: the percentage of stocks above their
moving averages, today's advancers vs decliners, and fresh highs/lows.

Pure functions on a wide DataFrame of daily closes (dates × symbols);
fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config


@dataclass(frozen=True)
class BreadthSnapshot:
    sample_size: int
    pct_above_50: float
    pct_above_200: float
    advancers: int
    decliners: int
    new_high_20d: int            # stocks at a 20-day high today
    new_low_20d: int

    @property
    def health(self) -> str:
        """'healthy' | 'mixed' | 'weak' based on the 200-day participation."""
        if self.pct_above_200 >= config.BREADTH_HEALTHY:
            return "healthy"
        if self.pct_above_200 <= config.BREADTH_WEAK:
            return "weak"
        return "mixed"


def pct_above_ma(closes: pd.DataFrame, window: int) -> pd.Series:
    """For every date: % of symbols (with enough history) above their MA."""
    if closes.empty:
        return pd.Series(dtype=float)
    ma = closes.rolling(window, min_periods=window).mean()
    valid = ma.notna()
    above = (closes > ma) & valid
    counts = valid.sum(axis=1)
    pct = above.sum(axis=1) / counts.replace(0, np.nan) * 100.0
    return pct.dropna()


def advance_decline(closes: pd.DataFrame) -> tuple[int, int]:
    """(advancers, decliners) on the latest session."""
    if len(closes) < 2:
        return 0, 0
    change = closes.iloc[-1] - closes.iloc[-2]
    change = change.dropna()
    return int((change > 0).sum()), int((change < 0).sum())


def new_highs_lows(closes: pd.DataFrame, window: int = 20) -> tuple[int, int]:
    """Stocks whose latest close is the highest / lowest of the last `window` days."""
    if len(closes) < window:
        return 0, 0
    recent = closes.tail(window)
    last = recent.iloc[-1]
    highs = int((last >= recent.max()).fillna(False).sum())
    lows = int((last <= recent.min()).fillna(False).sum())
    return highs, lows


def build_snapshot(closes: pd.DataFrame) -> BreadthSnapshot | None:
    """Latest breadth reading, or None when there is no usable data."""
    if closes.empty or len(closes) < 2:
        return None
    above_50 = pct_above_ma(closes, 50)
    above_200 = pct_above_ma(closes, 200)
    advancers, decliners = advance_decline(closes)
    highs, lows = new_highs_lows(closes)
    return BreadthSnapshot(
        sample_size=int(closes.iloc[-1].notna().sum()),
        pct_above_50=float(above_50.iloc[-1]) if not above_50.empty else 0.0,
        pct_above_200=float(above_200.iloc[-1]) if not above_200.empty else 0.0,
        advancers=advancers,
        decliners=decliners,
        new_high_20d=highs,
        new_low_20d=lows,
    )
