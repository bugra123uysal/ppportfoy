"""Yield curve and credit spread reads -- top-down macro signals.

Two things professional/institutional traders check before anything else:
whether the curve is inverted (10-year yield below the 3-month bill --
the New York Fed's own recession-probability model uses this exact 3m10y
spread, arguably more predictive than the more commonly-cited 2s10s), and
whether credit spreads are widening (high-yield corporate bonds
underperforming investment-grade ones -- a sign the market is pricing in
more default risk before it shows up in equities).

Both are free via yfinance -- no FRED API key, no paid data. Pure
functions only; fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config


@dataclass(frozen=True)
class YieldCurveSnapshot:
    yield_10y: float | None
    yield_3m: float | None
    spread_10y_3m: float | None            # percentage points; negative = inverted
    inverted: bool
    credit_spread_proxy_change: float | None  # % change in HYG/LQD ratio over the lookback
    credit_stress: bool


def credit_spread_proxy_change(
    hy_close: pd.Series, ig_close: pd.Series, lookback: int = config.CREDIT_SPREAD_LOOKBACK
) -> float | None:
    """% change in the (high-yield / investment-grade) bond ETF ratio over `lookback`
    sessions. A falling ratio means high-yield is underperforming investment-grade --
    spreads are widening, i.e. the market wants more compensation for credit risk.
    """
    ratio = (hy_close / ig_close).dropna()
    if len(ratio) < lookback + 1:
        return None
    start = float(ratio.iloc[-lookback - 1])
    end = float(ratio.iloc[-1])
    if start <= 0:
        return None
    return (end / start - 1.0) * 100.0


def build_yield_curve_snapshot(
    yield_10y: float | None,
    yield_3m: float | None,
    credit_change_pct: float | None,
) -> YieldCurveSnapshot:
    spread = (yield_10y - yield_3m) if yield_10y is not None and yield_3m is not None else None
    inverted = spread is not None and spread < 0
    stress = credit_change_pct is not None and credit_change_pct <= config.CREDIT_STRESS_THRESHOLD
    return YieldCurveSnapshot(
        yield_10y=yield_10y,
        yield_3m=yield_3m,
        spread_10y_3m=spread,
        inverted=inverted,
        credit_spread_proxy_change=credit_change_pct,
        credit_stress=stress,
    )
