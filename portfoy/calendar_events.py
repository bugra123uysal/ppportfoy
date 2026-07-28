"""Economic calendar — the scheduled events that move markets.

Covers what can be known reliably without a paid feed:
  - FOMC decision days (the Fed publishes them a year ahead → config)
  - NFP, the US jobs report (always the first Friday of the month)
  - earnings dates for the user's holdings (from Yahoo, passed in)

CPI-style releases whose dates shift are deliberately left out rather
than guessed. Pure functions; no network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from . import config


@dataclass(frozen=True)
class MarketEvent:
    when: date
    kind: str                    # "fomc" | "nfp" | "earnings"
    symbol: str = ""             # set for earnings events

    def days_left(self, today: date) -> int:
        return (self.when - today).days


def next_nfp(today: date) -> date:
    """The next first-Friday-of-the-month on or after `today`."""
    candidate = _first_friday(today.year, today.month)
    if candidate >= today:
        return candidate
    year, month = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return _first_friday(year, month)


def upcoming_events(
    today: date,
    earnings: dict[str, date | None] | None = None,
    lookahead_days: int = config.CALENDAR_LOOKAHEAD_DAYS,
) -> list[MarketEvent]:
    """Every known event inside the window, soonest first."""
    horizon = today + timedelta(days=lookahead_days)
    events: list[MarketEvent] = []

    for iso in config.FOMC_DATES_2026:
        fomc_day = date.fromisoformat(iso)
        if today <= fomc_day <= horizon:
            events.append(MarketEvent(fomc_day, "fomc"))

    nfp = next_nfp(today)
    while nfp <= horizon:
        events.append(MarketEvent(nfp, "nfp"))
        nfp = next_nfp(nfp + timedelta(days=1))

    for symbol, earnings_day in (earnings or {}).items():
        if earnings_day is not None and today <= earnings_day <= horizon:
            events.append(MarketEvent(earnings_day, "earnings", symbol=symbol))

    return sorted(events, key=lambda e: (e.when, e.kind))


def _first_friday(year: int, month: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(4 - first.weekday()) % 7)
