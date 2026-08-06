"""Fundamental valuation/quality/growth scan -- the "how would a fundamental
analyst pick this stock" counterpart to trade_scan.py's technical setups and
money_flow.py's volume/ownership signals.

Combines two free, complementary reads per stock (data.get_fundamentals):
valuation (P/E, PEG, EV/EBITDA) and quality/growth (revenue growth, margins,
ROE, debt/equity, FCF yield). This is not a buy/sell signal -- see
`classify_valuation`'s docstring for what the verdict does and doesn't mean.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config, data


@dataclass(frozen=True)
class FundamentalSnapshot:
    symbol: str
    sector: str
    pe: float | None
    peg: float | None
    ev_ebitda: float | None
    revenue_growth: float | None
    gross_margin: float | None
    operating_margin: float | None
    roe: float | None
    debt_to_equity: float | None
    fcf_yield: float | None
    verdict: str    # "ucuz" | "makul" | "pahali" | "belirsiz"


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


def build_fundamental_scan(universe: dict[str, str]) -> list[FundamentalSnapshot]:
    """Scan `universe` (ticker -> sector label) for fundamental metrics."""
    results: list[FundamentalSnapshot] = []
    for symbol, sector in universe.items():
        m = data.get_fundamentals(symbol)
        if m is None:
            continue
        verdict = classify_valuation(m.peg, m.ev_ebitda, m.revenue_growth, m.operating_margin)
        results.append(
            FundamentalSnapshot(
                symbol=symbol,
                sector=sector,
                pe=m.pe,
                peg=m.peg,
                ev_ebitda=m.ev_ebitda,
                revenue_growth=m.revenue_growth,
                gross_margin=m.gross_margin,
                operating_margin=m.operating_margin,
                roe=m.roe,
                debt_to_equity=m.debt_to_equity,
                fcf_yield=m.fcf_yield,
                verdict=verdict,
            )
        )
    return results
