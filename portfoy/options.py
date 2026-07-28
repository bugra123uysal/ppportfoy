"""Options activity maths — aggregating call/put volume per underlying.

Pure functions on already-fetched option-chain DataFrames; the network
fetch lives in data.py. Volume is contracts traded today (Yahoo, ~15 min
delayed); open interest is contracts outstanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import config


@dataclass(frozen=True)
class OptionActivity:
    symbol: str
    expiry: str                      # ISO date of the scanned expiry
    call_volume: int
    put_volume: int
    call_oi: int
    put_oi: int
    top_contracts: list[dict] = field(default_factory=list)

    @property
    def total_volume(self) -> int:
        return self.call_volume + self.put_volume

    @property
    def put_call_ratio(self) -> float | None:
        if self.call_volume <= 0:
            return None
        return self.put_volume / self.call_volume


def aggregate_chain(
    calls: pd.DataFrame,
    puts: pd.DataFrame,
    top_n: int = config.OPTIONS_TOP_CONTRACTS,
) -> dict:
    """Volume/OI sums plus the most-traded contracts of one expiry's chain."""
    return {
        "call_volume": _column_sum(calls, "volume"),
        "put_volume": _column_sum(puts, "volume"),
        "call_oi": _column_sum(calls, "openInterest"),
        "put_oi": _column_sum(puts, "openInterest"),
        "top_contracts": _top_contracts(calls, puts, top_n),
    }


def build_activity(symbol: str, expiry: str, summary: dict) -> OptionActivity:
    return OptionActivity(
        symbol=symbol,
        expiry=expiry,
        call_volume=int(summary.get("call_volume", 0)),
        put_volume=int(summary.get("put_volume", 0)),
        call_oi=int(summary.get("call_oi", 0)),
        put_oi=int(summary.get("put_oi", 0)),
        top_contracts=list(summary.get("top_contracts", [])),
    )


def rank_by_volume(activities: list[OptionActivity]) -> list[OptionActivity]:
    """Busiest underlyings first; empty chains are dropped."""
    active = [a for a in activities if a.total_volume > 0]
    return sorted(active, key=lambda a: a.total_volume, reverse=True)


def pcr_mood(ratio: float | None) -> str:
    """'bearish' | 'bullish' | 'neutral' reading of a put/call ratio."""
    if ratio is None:
        return "neutral"
    if ratio >= config.PCR_BEARISH:
        return "bearish"
    if ratio <= config.PCR_BULLISH:
        return "bullish"
    return "neutral"


def _column_sum(frame: pd.DataFrame, column: str) -> int:
    if frame is None or frame.empty or column not in frame.columns:
        return 0
    total = pd.to_numeric(frame[column], errors="coerce").fillna(0).sum()
    return int(total)


def _top_contracts(calls: pd.DataFrame, puts: pd.DataFrame, top_n: int) -> list[dict]:
    frames = []
    for kind, frame in (("CALL", calls), ("PUT", puts)):
        if frame is None or frame.empty or "volume" not in frame.columns:
            continue
        sub = frame[["strike", "lastPrice", "volume", "openInterest", "impliedVolatility"]].copy()
        sub["type"] = kind
        frames.append(sub)
    if not frames:
        return []
    merged = pd.concat(frames, ignore_index=True)
    merged["volume"] = pd.to_numeric(merged["volume"], errors="coerce").fillna(0)
    merged = merged.sort_values("volume", ascending=False).head(top_n)
    return [
        {
            "type": row["type"],
            "strike": float(row["strike"]),
            "last": float(row["lastPrice"]) if pd.notna(row["lastPrice"]) else 0.0,
            "volume": int(row["volume"]),
            "oi": int(row["openInterest"]) if pd.notna(row["openInterest"]) else 0,
            "iv": float(row["impliedVolatility"]) if pd.notna(row["impliedVolatility"]) else 0.0,
        }
        for _, row in merged.iterrows()
    ]
