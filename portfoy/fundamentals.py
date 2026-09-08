"""Fundamental valuation classification -- the "how would a fundamental
analyst read this stock" counterpart to trade_scan.py's technical setups and
money_flow.py's volume/ownership signals. Used by position_health.py (Risk
& Uyarılar's per-holding read) against data.get_fundamentals's output.

This is not a buy/sell signal -- see `classify_valuation`'s docstring for
what the verdict does and doesn't mean.
"""

from __future__ import annotations

from . import config


def classify_valuation(
    peg: float | None,
    ev_ebitda: float | None,
    revenue_growth: float | None,
    operating_margin: float | None,
) -> str:
    """"ucuz"/"makul"/"pahali" from PEG + EV/EBITDA, "belirsiz" when neither
    is available.

    A statistically cheap multiple on a shrinking, unprofitable business is a
    value trap, not a bargain -- shrinking revenue combined with a negative
    operating margin caps the verdict at "pahali" regardless of how the
    multiples read, instead of calling it "ucuz".
    """
    signals: list[int] = []
    if peg is not None:
        if peg < config.FUNDAMENTALS_PEG_CHEAP:
            signals.append(1)
        elif peg > config.FUNDAMENTALS_PEG_EXPENSIVE:
            signals.append(-1)
        else:
            signals.append(0)
    if ev_ebitda is not None and ev_ebitda > 0:
        if ev_ebitda < config.FUNDAMENTALS_EV_EBITDA_CHEAP:
            signals.append(1)
        elif ev_ebitda > config.FUNDAMENTALS_EV_EBITDA_EXPENSIVE:
            signals.append(-1)
        else:
            signals.append(0)

    if not signals:
        return "belirsiz"

    deteriorating = (
        revenue_growth is not None and revenue_growth < 0
        and operating_margin is not None and operating_margin < 0
    )
    total = sum(signals)
    if deteriorating or total < 0:
        return "pahali"
    if total > 0:
        return "ucuz"
    return "makul"
