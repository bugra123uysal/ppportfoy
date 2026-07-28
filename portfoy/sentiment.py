"""Composite fear/greed score — self-computed, no external sentiment API.

Four components, each normalised to 0 (max fear) … 100 (max greed):

    vix       — implied volatility level, inverted
    momentum  — S&P 500 versus its ~6-month average
    breadth   — % of sample stocks above their 200-day average
    put_call  — SPY put/call volume ratio, inverted

The composite is the mean of whichever components are available, so one
failed data source degrades the score instead of killing it.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config

LABELS = ("extreme_fear", "fear", "neutral", "greed", "extreme_greed")


@dataclass(frozen=True)
class SentimentScore:
    composite: float             # 0..100
    components: dict             # name -> 0..100 (only the available ones)

    @property
    def label(self) -> str:
        if self.composite < 25:
            return "extreme_fear"
        if self.composite < 45:
            return "fear"
        if self.composite <= 55:
            return "neutral"
        if self.composite <= 75:
            return "greed"
        return "extreme_greed"


def vix_score(vix: float) -> float:
    span = config.SENT_VIX_PANIC - config.SENT_VIX_CALM
    return _clip((config.SENT_VIX_PANIC - vix) / span * 100.0)


def momentum_score(price: float, sma: float) -> float:
    """S&P vs SMA125: −10% below → 0, at the average → 50, +10% above → 100."""
    if sma <= 0:
        return 50.0
    diff_pct = (price / sma - 1.0) * 100.0
    return _clip(50.0 + diff_pct * 5.0)


def breadth_score(pct_above_200: float) -> float:
    return _clip(pct_above_200)


def put_call_score(ratio: float) -> float:
    span = config.SENT_PCR_FEAR - config.SENT_PCR_GREED
    return _clip((config.SENT_PCR_FEAR - ratio) / span * 100.0)


def build_score(
    vix: float | None = None,
    price: float | None = None,
    sma: float | None = None,
    pct_above_200: float | None = None,
    put_call: float | None = None,
) -> SentimentScore | None:
    """Composite from whatever inputs are present. None if nothing is."""
    components: dict[str, float] = {}
    if vix is not None:
        components["vix"] = vix_score(vix)
    if price is not None and sma is not None:
        components["momentum"] = momentum_score(price, sma)
    if pct_above_200 is not None:
        components["breadth"] = breadth_score(pct_above_200)
    if put_call is not None:
        components["put_call"] = put_call_score(put_call)
    if not components:
        return None
    return SentimentScore(
        composite=sum(components.values()) / len(components),
        components=components,
    )


def _clip(value: float) -> float:
    return max(0.0, min(100.0, value))
