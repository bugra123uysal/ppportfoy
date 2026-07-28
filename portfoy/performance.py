"""Benchmark comparison — how the portfolio did versus everything else.

Every price series is converted into one base currency before anything is
compared, so a TRY-quoted index (BIST 100) and a USD-quoted one (S&P 500)
are measured on the same ruler. Each series is then rebased to 100 at the
start of the window, which turns the chart into a straight "% return" race.

The portfolio line is a buy-and-hold simulation of the holdings you own
*today*: it answers "how would my current basket have performed over this
window", not "what did I actually earn" (which depends on when each lot was
bought). The realised P/L against your own cost basis is shown separately.

Pure functions — data fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from . import config


@dataclass(frozen=True)
class SeriesResult:
    key: str                 # symbol, or "portfolio"
    label_tr: str
    label_en: str
    return_pct: float
    series: pd.Series        # rebased to 100 at the window start

    def label(self, lang: str) -> str:
        return self.label_tr if lang == "tr" else self.label_en


def to_daily(series: pd.Series) -> pd.Series:
    """Collapse a price series onto plain, timezone-free calendar days.

    yfinance stamps each bar in its own exchange timezone — the S&P closes on
    New York time, BIST on Istanbul time, FX on UTC. Those timestamps never
    match each other exactly, so aligning them raw yields nothing. Normalising
    to dates first is what makes cross-market comparison possible at all.
    """
    clean = series.dropna()
    if clean.empty:
        return clean
    index = pd.DatetimeIndex(clean.index)
    if index.tz is not None:
        index = index.tz_convert("UTC").tz_localize(None)
    daily = pd.Series(clean.to_numpy(), index=index.normalize())
    return daily[~daily.index.duplicated(keep="last")].sort_index()


def convert(prices: pd.Series, quoted_in: str, base: str, usdtry: pd.Series) -> pd.Series:
    """Restate a price series in `base` currency using a USD/TRY series."""
    series = to_daily(prices)
    if quoted_in == base or series.empty:
        return series
    fx = to_daily(usdtry).reindex(series.index).ffill()
    converted = series * fx if base == "TRY" else series / fx
    return converted.dropna()


def window_start(index: pd.Index, period_key: str) -> pd.Timestamp | None:
    """First timestamp of the requested window, or None when data is too short."""
    if len(index) == 0:
        return None
    if period_key == "per_ytd":
        year_start = pd.Timestamp(date(pd.Timestamp(index[-1]).year, 1, 1))
        tz = getattr(index, "tz", None)
        if tz is not None:
            year_start = year_start.tz_localize(tz)
        inside = index[index >= year_start]
        return inside[0] if len(inside) else index[0]
    bars = config.COMPARE_PERIODS.get(period_key)
    if bars is None or len(index) <= bars:
        return index[0]
    return index[-bars - 1]


def rebase(series: pd.Series, start: pd.Timestamp | None) -> pd.Series:
    """Normalise a series to 100 at `start`."""
    clean = series.dropna()
    if start is not None:
        clean = clean[clean.index >= start]
    if clean.empty:
        return clean
    first = float(clean.iloc[0])
    if first == 0:
        return clean
    return 100.0 * clean / first


def total_return(series: pd.Series) -> float:
    """Percentage change across a rebased (or raw) series."""
    clean = series.dropna()
    if len(clean) < 2:
        return 0.0
    first = float(clean.iloc[0])
    if first == 0:
        return 0.0
    return (float(clean.iloc[-1]) / first - 1.0) * 100.0


def portfolio_series(
    weights: dict[str, float],
    prices: dict[str, pd.Series],
    currencies: dict[str, str],
    base: str,
    usdtry: pd.Series,
    start: pd.Timestamp | None,
    cash_weight: float = 0.0,
) -> pd.Series:
    """Weighted buy-and-hold index of the current holdings, rebased to 100.

    Cash is carried as a flat 100 line for its share of the portfolio, which
    correctly drags the return toward zero the more cash you hold.
    """
    components: list[pd.Series] = []
    total_weight = 0.0
    for symbol, weight in weights.items():
        series = prices.get(symbol)
        if series is None or weight <= 0:
            continue
        converted = convert(series, currencies.get(symbol, "USD"), base, usdtry)
        rebased = rebase(converted, start)
        if rebased.empty:
            continue
        components.append(rebased * weight)
        total_weight += weight
    if not components:
        return pd.Series(dtype=float)

    combined = pd.concat(components, axis=1).ffill().dropna()
    if combined.empty:
        return pd.Series(dtype=float)
    index = combined.sum(axis=1)
    if cash_weight > 0:
        index = index + 100.0 * cash_weight
        total_weight += cash_weight
    return index / total_weight if total_weight > 0 else index


def compare(
    portfolio: pd.Series,
    benchmark_prices: dict[str, pd.Series],
    base: str,
    usdtry: pd.Series,
    period_key: str,
    lang_labels: dict[str, tuple[str, str, str]] | None = None,
) -> list[SeriesResult]:
    """Portfolio plus every benchmark, rebased and ranked best-first."""
    labels = lang_labels if lang_labels is not None else config.BENCHMARKS
    results: list[SeriesResult] = []

    if not portfolio.empty:
        results.append(
            SeriesResult("portfolio", "Portföyüm", "My Portfolio",
                         total_return(portfolio), portfolio)
        )

    for symbol, prices in benchmark_prices.items():
        label_tr, label_en, quoted_in = labels.get(symbol, (symbol, symbol, "USD"))
        converted = convert(prices, quoted_in, base, usdtry)
        start = window_start(converted.index, period_key)
        rebased = rebase(converted, start)
        if len(rebased) < 2:
            continue
        results.append(
            SeriesResult(symbol, label_tr, label_en, total_return(rebased), rebased)
        )
    return sorted(results, key=lambda r: r.return_pct, reverse=True)
