"""Rotation + My Trade overlap.

Cross-references the sector-rotation candidate pool (a stock that's a top-5
1-month performer within its curated pool, and whose sector currently sits
in the RRG's leading/improving quadrant -- see rotation.py) against My
Trade's own bullish signals: the indicator screener's long entries, VCP
breakout candidates, and money-flow accumulation reads (see trade_scan.py,
vcp_scan.py, money_flow.py).

A stock surfacing here means two independently-built scans -- one reading
sector-relative price action, the others reading a single stock's own
technicals/volume -- happen to agree it's worth a look right now. That is
corroboration, not a stronger guarantee than either scan alone; still a
mechanical rule combination, not investment advice.

Pure function -- callers pass in results already computed by rotation.py,
trade_scan.py, vcp_scan.py and money_flow.py, so this module fetches
nothing itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .money_flow import MoneyFlowSignal
from .rotation import IMPROVING, LEADING, SectorLeader, SectorRotation
from .trade_scan import TradeSignal
from .vcp_scan import VcpCandidate

ROTATE_IN_QUADRANTS = (LEADING, IMPROVING)


@dataclass(frozen=True)
class OverlapCandidate:
    symbol: str
    sector: str                # Turkish sector label, e.g. "Enerji"
    perf_1m: float              # sector-leader ranking field, from rotation.py
    signals: tuple[str, ...]    # which My Trade scanner(s) agree, e.g. ("trade_scan_long",)


def build_rotation_overlap(
    sectors: list[SectorRotation],
    leaders: dict[str, list[SectorLeader]],
    trade_signals: list[TradeSignal],
    vcp_candidates: list[VcpCandidate],
    money_flow_signals: list[MoneyFlowSignal],
) -> list[OverlapCandidate]:
    """Sector-leader stocks in a leading/improving sector that at least one
    My Trade scanner also flags bullish. Sorted by how many scanners agree,
    then by 1-month sector-leader performance.
    """
    promising = {s.symbol for s in sectors if s.quadrant in ROTATE_IN_QUADRANTS}
    if not promising:
        return []

    pool: dict[str, tuple[str, float]] = {}
    for etf in promising:
        for leader in leaders.get(etf, []):
            pool[leader.symbol] = (etf, leader.perf_1m)
    if not pool:
        return []

    long_symbols = {s.symbol for s in trade_signals if s.direction == "long"}
    vcp_symbols = {c.symbol for c in vcp_candidates}
    accumulation_symbols = {
        m.symbol for m in money_flow_signals if m.cmf_signal == "accumulation"
    }

    results: list[OverlapCandidate] = []
    for symbol, (etf, perf_1m) in pool.items():
        signals: list[str] = []
        if symbol in long_symbols:
            signals.append("trade_scan_long")
        if symbol in vcp_symbols:
            signals.append("vcp")
        if symbol in accumulation_symbols:
            signals.append("money_flow_accumulation")
        if not signals:
            continue
        sector_label = config.SECTOR_ETFS.get(etf, (etf, etf))[0]
        results.append(
            OverlapCandidate(
                symbol=symbol, sector=sector_label, perf_1m=perf_1m, signals=tuple(signals)
            )
        )

    return sorted(results, key=lambda c: (-len(c.signals), -c.perf_1m))
