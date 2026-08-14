"""Fibonacci retracement/extension levels for the Hisse Raporu single-symbol
report -- pure OHLCV math against an already-fetched DataFrame, same
"pure functions only, fetching stays in data.py" split as money_flow.py/
report.py.

Retracement levels measure how far price has pulled back from the most
recent swing high/low; extension levels project how far it could travel
beyond that swing. Direction is inferred from which swing point (the
window's high or its low) happened more recently -- whichever one is later
is the "current" extreme price is retracing away from.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config

# Below this many bars, a "swing" isn't meaningful -- too easy for the
# window's only high/low to just be noise from a couple of sessions.
_MIN_WINDOW_BARS = 10


@dataclass(frozen=True)
class FibLevel:
    ratio: float
    price: float
    kind: str            # "retracement" | "extension"
    label: str


@dataclass(frozen=True)
class FibLevels:
    swing_high: float
    swing_low: float
    swing_high_date: str         # ISO date
    swing_low_date: str          # ISO date
    direction: str                # "yukselis" | "dusus"
    lookback_days: int
    levels: list[FibLevel]
    nearest_ratio: float
    nearest_price: float
    pct_to_nearest: float         # signed %, last close vs. the nearest level
    at_level: bool                # within config.FIB_NEAR_LEVEL_PCT of nearest_price
    zone_label: str


def _fmt_ratio(ratio: float) -> str:
    text = f"{ratio:.3f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _level_label(ratio: float, kind: str) -> str:
    suffix = "geri çekilme" if kind == "retracement" else "uzantı"
    return f"{_fmt_ratio(ratio)} {suffix}"


def _levels_for_swing(swing_high: float, swing_low: float, direction: str) -> list[FibLevel]:
    span = swing_high - swing_low
    levels: list[FibLevel] = []
    for ratio in config.FIB_RETRACEMENT_RATIOS:
        price = (
            swing_high - span * ratio if direction == "yukselis" else swing_low + span * ratio
        )
        label = _level_label(ratio, "retracement")
        levels.append(FibLevel(ratio=ratio, price=price, kind="retracement", label=label))
    for ratio in config.FIB_EXTENSION_RATIOS:
        price = (
            swing_high + span * (ratio - 1)
            if direction == "yukselis"
            else swing_low - span * (ratio - 1)
        )
        label = _level_label(ratio, "extension")
        levels.append(FibLevel(ratio=ratio, price=price, kind="extension", label=label))
    return levels


def _zone_label(levels: list[FibLevel], last_close: float, direction: str) -> str:
    """Which pair of adjacent retracement ratios `last_close` sits between,
    in ratio order (0.236 -> 0.786) regardless of whether price itself rises
    or falls as the ratio grows. Beyond the outer levels, "0 altında" reads
    as "less pulled back than the shallowest level plotted" and
    "{max} üzerinde" as "pulled back further than the deepest one plotted"."""
    retracements = [lvl for lvl in levels if lvl.kind == "retracement"]
    first, last = retracements[0], retracements[-1]
    shallow_edge, deep_edge = (
        (last_close >= first.price, last_close <= last.price)
        if direction == "yukselis"
        else (last_close <= first.price, last_close >= last.price)
    )
    if shallow_edge:
        return "0 altında"
    if deep_edge:
        return f"{_fmt_ratio(last.ratio)} üzerinde"
    for lo, hi in zip(retracements, retracements[1:]):  # noqa: B905 -- pairwise, uneven by design
        low_price, high_price = sorted((lo.price, hi.price))
        if low_price <= last_close <= high_price:
            return f"{_fmt_ratio(lo.ratio)} - {_fmt_ratio(hi.ratio)} arası"
    # Unreachable -- the two edge checks above cover every remaining case.
    return f"{_fmt_ratio(last.ratio)} üzerinde"  # pragma: no cover


def build_levels(df: pd.DataFrame, lookback_days: int) -> FibLevels | None:
    if df.empty:
        return None

    window = df.tail(lookback_days)
    if len(window) < _MIN_WINDOW_BARS:
        return None

    high = window["High"].dropna()
    low = window["Low"].dropna()
    close = window["Close"].dropna()
    if len(high) < 2 or len(low) < 2 or close.empty:
        return None

    swing_high = float(high.max())
    swing_low = float(low.min())
    if swing_high <= swing_low:
        return None

    swing_high_date = high.idxmax()
    swing_low_date = low.idxmin()
    direction = "yukselis" if swing_high_date > swing_low_date else "dusus"

    levels = _levels_for_swing(swing_high, swing_low, direction)

    last_close = float(close.iloc[-1])
    nearest = min(levels, key=lambda lvl: abs(lvl.price - last_close))
    pct_to_nearest = (last_close / nearest.price - 1.0) * 100.0 if nearest.price else 0.0

    return FibLevels(
        swing_high=swing_high,
        swing_low=swing_low,
        swing_high_date=swing_high_date.date().isoformat(),
        swing_low_date=swing_low_date.date().isoformat(),
        direction=direction,
        lookback_days=lookback_days,
        levels=levels,
        nearest_ratio=nearest.ratio,
        nearest_price=nearest.price,
        pct_to_nearest=pct_to_nearest,
        at_level=abs(pct_to_nearest) <= config.FIB_NEAR_LEVEL_PCT,
        zone_label=_zone_label(levels, last_close, direction),
    )
