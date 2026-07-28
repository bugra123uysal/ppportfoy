"""Sector rotation maths — Relative Rotation Graph (RRG).

An RRG places each sector on two axes measured against a benchmark (SPY):

    x = RS-Ratio     → relative strength   (>100 stronger than the market)
    y = RS-Momentum  → relative momentum   (>100 strength is still improving)

That splits the plane into four quadrants, and a sector normally travels
clockwise through them: improving → leading → weakening → lagging.
Drawing the last few weeks as a tail shows *where a sector came from*.

The original JdK RS-Ratio formula is proprietary. This module uses the
cross-sectional variant: each week every sector is scored against the
*other sectors* (z-score of its relative performance), so the strongest
names sit on the right and the ones gaining steam sit at the top. That is
what makes the picture readable — a sector that steadily beats the market
stays in the leading quadrant instead of drifting back to the centre.

Pure functions only — data fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config

LEADING = "leading"
WEAKENING = "weakening"
LAGGING = "lagging"
IMPROVING = "improving"

# Clockwise order, used to decide whether a move is the "normal" rotation.
_CYCLE = (IMPROVING, LEADING, WEAKENING, LAGGING)

# Cross-sectional scoring needs a few peers to be meaningful.
MIN_SYMBOLS = 3


@dataclass(frozen=True)
class SectorRotation:
    symbol: str
    label_tr: str
    label_en: str
    tail_x: list[float]          # RS-Ratio, oldest → newest
    tail_y: list[float]          # RS-Momentum, oldest → newest
    quadrant: str                # where it is now
    prev_quadrant: str           # where the tail started
    perf_1w: float               # % price change over the trailing windows
    perf_1m: float
    perf_3m: float

    @property
    def x(self) -> float:
        return self.tail_x[-1]

    @property
    def y(self) -> float:
        return self.tail_y[-1]

    @property
    def has_moved(self) -> bool:
        return self.quadrant != self.prev_quadrant

    def label(self, lang: str) -> str:
        return self.label_tr if lang == "tr" else self.label_en


def classify(rs_ratio: float, rs_momentum: float) -> str:
    """Which quadrant a point falls in."""
    if rs_ratio >= 100.0:
        return LEADING if rs_momentum >= 100.0 else WEAKENING
    return IMPROVING if rs_momentum >= 100.0 else LAGGING


def is_clockwise(previous: str, current: str) -> bool:
    """True when the move follows the healthy improving→leading→… cycle."""
    if previous == current:
        return True
    return _CYCLE[(_CYCLE.index(previous) + 1) % len(_CYCLE)] == current


def build_rotation(
    closes: pd.DataFrame,
    labels: dict[str, tuple[str, str]],
    benchmark: str = config.RRG_BENCHMARK,
    tail: int = config.RRG_TAIL_WEEKS,
    reference: list[str] | None = None,
) -> list[SectorRotation]:
    """One SectorRotation per column in `closes` (the benchmark is excluded).

    `closes` holds weekly closing prices indexed by date. `reference` pins the
    scoring universe — see cross_normalize. Returns an empty list when the
    benchmark is missing or there is not enough history.
    """
    ratio, momentum = rrg_frames(closes, benchmark, reference=reference)
    if ratio.empty or len(ratio) < 2:
        return []

    tail_length = max(tail, 2)
    x_tail = ratio.tail(tail_length)
    y_tail = momentum.tail(tail_length)

    results: list[SectorRotation] = []
    for symbol in ratio.columns:
        xs = [float(v) for v in x_tail[symbol]]
        ys = [float(v) for v in y_tail[symbol]]
        if any(pd.isna(v) for v in xs + ys):
            continue
        label_tr, label_en = labels.get(symbol, (symbol, symbol))
        prices = closes[symbol].dropna()
        results.append(
            SectorRotation(
                symbol=symbol,
                label_tr=label_tr,
                label_en=label_en,
                tail_x=xs,
                tail_y=ys,
                quadrant=classify(xs[-1], ys[-1]),
                prev_quadrant=classify(xs[0], ys[0]),
                perf_1w=_pct_change(prices, 1),
                perf_1m=_pct_change(prices, 4),
                perf_3m=_pct_change(prices, 13),
            )
        )
    return sorted(results, key=lambda r: (-r.x, -r.y))


def rrg_frames(
    closes: pd.DataFrame,
    benchmark: str = config.RRG_BENCHMARK,
    ratio_window: int = config.RRG_RATIO_WINDOW,
    momentum_window: int = config.RRG_MOMENTUM_WINDOW,
    reference: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """RS-Ratio and RS-Momentum matrices (dates × symbols), already normalised."""
    strength, momentum = raw_rrg_frames(closes, benchmark, ratio_window, momentum_window)
    if strength.empty:
        return strength, momentum
    return (
        cross_normalize(strength, reference),
        cross_normalize(momentum, reference),
    )


def raw_rrg_frames(
    closes: pd.DataFrame,
    benchmark: str = config.RRG_BENCHMARK,
    ratio_window: int = config.RRG_RATIO_WINDOW,
    momentum_window: int = config.RRG_MOMENTUM_WINDOW,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Un-normalised inputs.

    strength = relative performance versus the benchmark over `ratio_window`
               weeks (100 = matched the market).
    momentum = that strength measured against its own recent average, i.e.
               whether the outperformance is accelerating.
    """
    empty = pd.DataFrame()
    if closes.empty or benchmark not in closes.columns:
        return empty, empty
    symbols = [c for c in closes.columns if c != benchmark]
    if len(symbols) < MIN_SYMBOLS:
        return empty, empty

    bench = closes[benchmark]
    rs = closes[symbols].div(bench, axis=0)
    strength = 100.0 * rs / rs.shift(ratio_window)
    momentum = (
        100.0
        * strength
        / strength.rolling(momentum_window, min_periods=momentum_window).mean()
    )
    valid = strength.notna().any(axis=1) & momentum.notna().any(axis=1)
    return strength[valid], momentum[valid]


def cross_normalize(
    frame: pd.DataFrame,
    reference: list[str] | None = None,
    clip: float = config.RRG_CLIP,
) -> pd.DataFrame:
    """Z-score each row across symbols, recentred on 100 (the RRG convention).

    Comparing sectors against each other — rather than against their own
    history — is what keeps a persistent leader on the right-hand side.

    `reference` pins which columns define the mean and standard deviation.
    Everything else is scored against that same yardstick, so overlaying
    extra symbols (a user's individual holdings, which are far more volatile
    than sector ETFs) cannot shift where the sectors themselves plot.

    Scores are capped at ±`clip` sigma. Reference symbols never come close to
    that bound, so the cap only pins wild outliers to the edge of the map
    instead of letting them stretch the axes into unreadability.
    """
    if frame.empty:
        return frame
    columns = [c for c in (reference or []) if c in frame.columns]
    basis = frame[columns] if len(columns) >= MIN_SYMBOLS else frame
    mean = basis.mean(axis=1)
    std = basis.std(axis=1)
    centred = frame.sub(mean, axis=0).div(std.where(std > 0), axis=0)
    return 100.0 + centred.fillna(0.0).clip(-clip, clip)


def _pct_change(series: pd.Series, periods: int) -> float:
    if len(series) <= periods:
        return 0.0
    previous = float(series.iloc[-1 - periods])
    if previous == 0:
        return 0.0
    return (float(series.iloc[-1]) / previous - 1.0) * 100.0
