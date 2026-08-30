"""Trend Bulucu + My Trade overlap ("TradingView Tarama").

Cross-references Trend Bulucu's market-structure trend candidates
(trend_scan.py) against My Trade's indicator screener (trade_scan.py) over
config.SP500_NASDAQ100_STOCKS (~500 names -- see that constant's own
docstring): a symbol surfaces here only when both scans agree on the *same*
direction -- a bullish (boğa) trend structure with an active long setup, or
a bearish (ayı) trend structure with an active short setup.

Two independently-built mechanical scans -- one reading swing-point market
structure, the other reading momentum/volume/band indicators -- agreeing on
the same symbol and direction is corroboration, not a stronger guarantee
than either scan alone. Still a mechanical rule combination, not investment
advice.

Despite the page name, this does not read anything from the TradingView
desktop app itself -- a deployed web app has no way to reach a user's local
TradingView Desktop process. It's the same free Yahoo-data pipeline the rest
of My Trade uses, just over a much larger universe. The name reflects the
intended workflow: the same S&P 500 + Nasdaq-100 universe also lives in the
user's own TradingView watchlist (pushed there manually, once) so they can
browse the full list and its charts directly in TradingView, while this page
reports which of those names are worth a closer look right now.

Pure function -- `build_trend_trade_overlap` takes results already computed
by trend_scan.py and trade_scan.py. `build_trend_trade_overlap_scan` is the
one function here that fetches, and only because it needs to share one
history fetch between both underlying scans (see its own docstring).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data
from .trade_scan import TradeSignal
from .trade_scan import scan_symbol as _trade_scan_symbol
from .trend_scan import AYI, BOGA, TrendCandidate
from .trend_scan import scan_symbol as _trend_scan_symbol

_TRADE_DIRECTION_BY_TREND = {BOGA: "long", AYI: "short"}


@dataclass(frozen=True)
class TrendTradeCandidate:
    symbol: str
    sector: str
    price: float
    change_1d: float
    direction: str                  # "boga" | "ayi" -- trend_scan's own label
    trend_score: int                # 1..3, trend_scan's own score
    trend_strength: str             # "erken" | "olusuyor" | "guclu"
    trade_groups: list[int]         # which My Trade groups (1-4) confirm, same direction
    structural_stop: float | None   # trend_scan's swing-based stop
    suggested_stop: float | None    # trade_scan's ATR-based stop, same direction


def build_trend_trade_overlap(
    trend_candidates: list[TrendCandidate], trade_signals: list[TradeSignal]
) -> list[TrendTradeCandidate]:
    """Trend candidates whose direction also has a matching My Trade signal
    on the same symbol. Sorted by trend score, then how many My Trade groups
    confirm, then trailing 1-day move -- strongest corroboration first."""
    trade_by_key = {(s.symbol, s.direction): s for s in trade_signals}

    results: list[TrendTradeCandidate] = []
    for trend in trend_candidates:
        trade = trade_by_key.get((trend.symbol, _TRADE_DIRECTION_BY_TREND[trend.direction]))
        if trade is None:
            continue
        results.append(
            TrendTradeCandidate(
                symbol=trend.symbol,
                sector=trend.sector,
                price=trend.price,
                change_1d=trend.change_1d,
                direction=trend.direction,
                trend_score=trend.score,
                trend_strength=trend.strength,
                trade_groups=trade.groups,
                structural_stop=trend.structural_stop,
                suggested_stop=trade.suggested_stop,
            )
        )

    return sorted(results, key=lambda c: (-c.trend_score, -len(c.trade_groups), -c.change_1d))


def build_trend_trade_overlap_scan(universe: dict[str, str]) -> list[TrendTradeCandidate]:
    """Scan `universe` and combine, fetching each symbol's history only
    once. trend_scan and trade_scan both fetch config.TREND_HISTORY_PERIOD /
    config.TRADE_SCAN_HISTORY_PERIOD independently -- both currently "1y",
    so calling build_trend_scan(universe) + build_trade_scan(universe) here
    would download the same ~500-symbol history twice for no reason. Reuses
    each module's own scan_symbol(symbol, sector, df) instead (same
    pre-fetched-df pattern position_health.py uses against a small universe;
    this one matters more at SP500_NASDAQ100_STOCKS's scale)."""
    histories = data.get_histories(tuple(universe), period=config.TREND_HISTORY_PERIOD)

    trend_candidates: list[TrendCandidate] = []
    trade_signals: list[TradeSignal] = []
    for symbol, sector in universe.items():
        df = histories.get(symbol, pd.DataFrame())
        trend_candidate = _trend_scan_symbol(symbol, sector, df)
        if trend_candidate is not None:
            trend_candidates.append(trend_candidate)
        trade_signals.extend(_trade_scan_symbol(symbol, sector, df))

    return build_trend_trade_overlap(trend_candidates, trade_signals)


def _describe(c: TrendTradeCandidate) -> str:
    groups = "/".join(f"G{g}" for g in c.trade_groups)
    return (
        f"{c.symbol} ({c.sector}, {c.price:.2f}, {c.change_1d:+.1f}%, "
        f"trend {c.trend_strength} {c.trend_score}/3, My Trade {groups})"
    )


def render_text_report(candidates: list[TrendTradeCandidate]) -> str:
    """Deterministic Turkish prose summary of the overlap. Unlike
    commentary.py's AI narration (optional, can come back None without an
    NVIDIA_API_KEY), this always renders something -- it's the panel's
    primary output, a written report instead of a big sortable table."""
    if not candidates:
        return (
            "Şu an Trend Bulucu'nun piyasa yapısı taraması ile My Trade'in "
            "indikatör sinyali aynı yönde kesişen bir hisse yok."
        )

    bullish = [c for c in candidates if c.direction == BOGA]
    bearish = [c for c in candidates if c.direction == AYI]

    lines = [
        f"{len(candidates)} hisse bulundu ({len(bullish)} boğa, {len(bearish)} ayı yönünde) -- "
        "Trend Bulucu'nun piyasa yapısı taraması ile My Trade'in indikatör sinyali aynı yönü "
        "işaret ediyor."
    ]
    if bullish:
        lines.append("Boğa yönünde: " + "; ".join(_describe(c) for c in bullish) + ".")
    if bearish:
        lines.append("Ayı yönünde: " + "; ".join(_describe(c) for c in bearish) + ".")
    return "\n\n".join(lines)
