"""Per-holding "is this position weakening?" read.

Applies the same technical (trade_scan), money-flow (money_flow), and
fundamental (fundamentals) signals My Trade's scanners already run against
the fixed sector-leader universe -- but to the user's own portfolio instead,
on Risk & Uyarılar. Not a sell signal: a mechanical summary of the same
free, public signals already shown elsewhere in the app, applied to what the
user actually holds.

Reuses `df` from api_data._load_metrics's already-fetched histories, so this
costs zero extra price-history network calls -- only `data.get_fundamentals`
is a genuinely separate (cached) fetch, since valuation data isn't part of
OHLCV history.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data
from .fundamentals import classify_valuation
from .money_flow import scan_symbol as money_flow_scan_symbol
from .trade_scan import scan_symbol as trade_scan_symbol


@dataclass(frozen=True)
class PositionHealth:
    symbol: str
    score: int              # negative = weakening, positive = strengthening
    reasons: list[str]
    verdict: str             # "zayifliyor" | "notr" | "guclu"


def _verdict(score: int) -> str:
    if score <= config.POSITION_HEALTH_WEAKENING:
        return "zayifliyor"
    if score >= config.POSITION_HEALTH_STRONG:
        return "guclu"
    return "notr"


def evaluate_position(symbol: str, df: pd.DataFrame) -> PositionHealth | None:
    """None when there isn't enough history to say anything -- Risk &
    Uyarılar should stay silent on a position rather than show a false
    "neutral" reading for it.
    """
    if df.empty:
        return None

    score = 0
    reasons: list[str] = []

    short_signals = [s for s in trade_scan_symbol(symbol, "", df) if s.direction == "short"]
    if short_signals:
        score -= len(short_signals)
        groups = sorted({g for s in short_signals for g in s.groups})
        group_list = ", ".join(str(g) for g in groups)
        reasons.append(f"{len(groups)} teknik satış sinyali eşleşti (Grup {group_list})")

    money_flow = money_flow_scan_symbol(symbol, "", df)
    if money_flow is not None and money_flow.cmf_signal == "distribution":
        score -= 1
        reasons.append("Sermaye çıkışı (dağıtım) görülüyor -- CMF negatif")

    fundamentals = data.get_fundamentals(symbol)
    if fundamentals is not None:
        verdict = classify_valuation(
            fundamentals.peg, fundamentals.ev_ebitda,
            fundamentals.revenue_growth, fundamentals.operating_margin,
        )
        if verdict == "pahali":
            score -= 1
            reasons.append("Değerleme pahalı görünüyor (PEG/FD-FAVÖK)")
        elif verdict == "ucuz":
            score += 1
            reasons.append("Değerleme hâlâ ucuz görünüyor (PEG/FD-FAVÖK)")

    return PositionHealth(symbol=symbol, score=score, reasons=reasons, verdict=_verdict(score))


def evaluate_portfolio(
    symbols: list[str], histories: dict[str, pd.DataFrame]
) -> list[PositionHealth]:
    out: list[PositionHealth] = []
    for symbol in symbols:
        health = evaluate_position(symbol, histories.get(symbol, pd.DataFrame()))
        if health is not None:
            out.append(health)
    return out
