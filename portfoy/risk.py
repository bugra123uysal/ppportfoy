"""Portfolio metrics and the alert engine.

Pure functions: they take already-fetched data (quotes, histories, FX)
and return metric rows / Alert records. No network access here, which
keeps everything unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

import pandas as pd

from . import config
from .indicators import atr, last_value, rsi, sma
from .storage import CashHolding, Position

SEVERITIES = ("crit", "warn", "info")


@dataclass(frozen=True)
class Alert:
    severity: str        # "crit" | "warn" | "info"
    key: str             # i18n template key (al_*)
    params: dict


@dataclass(frozen=True)
class PositionMetrics:
    symbol: str
    currency: str
    quantity: float
    avg_cost: float
    price: float
    change_pct: float          # daily
    value: float               # in own currency
    value_try: float
    value_usd: float
    pnl: float                 # in own currency
    pnl_pct: float
    weight: float              # share of total portfolio value (0..1)
    rsi: float | None
    sma_fast: float | None
    sma_slow: float | None
    atr_stop: float | None     # suggested stop level (price - k*ATR)


def to_try(amount: float, currency: str, usdtry: float | None) -> float:
    if currency == "TRY" or not usdtry:
        return amount if currency == "TRY" else 0.0
    return amount * usdtry


def to_usd(amount: float, currency: str, usdtry: float | None) -> float:
    if currency == "USD":
        return amount
    return amount / usdtry if usdtry else 0.0


def cash_totals(cash: list[CashHolding], usdtry: float | None) -> dict:
    """Cash balances expressed in both currencies."""
    return {
        "try": sum(to_try(c.amount, c.currency, usdtry) for c in cash),
        "usd": sum(to_usd(c.amount, c.currency, usdtry) for c in cash),
    }


def compute_metrics(
    positions: list[Position],
    quotes: dict,
    histories: dict[str, pd.DataFrame],
    usdtry: float | None,
    cash_usd: float = 0.0,
) -> list[PositionMetrics]:
    """Build one metrics row per position that has a live quote.

    `cash_usd` joins the weight denominator so a position's weight is its
    share of the whole portfolio, cash included.
    """
    rows = []
    for pos in positions:
        q = quotes.get(pos.symbol)
        if q is None or q.price <= 0:
            continue
        hist = histories.get(pos.symbol, pd.DataFrame())
        ind = _indicators_for(hist)
        value = pos.quantity * q.price
        cost = pos.quantity * pos.avg_cost
        rows.append(
            PositionMetrics(
                symbol=pos.symbol,
                currency=pos.currency,
                quantity=pos.quantity,
                avg_cost=pos.avg_cost,
                price=q.price,
                change_pct=q.change_pct,
                value=value,
                value_try=to_try(value, pos.currency, usdtry),
                value_usd=to_usd(value, pos.currency, usdtry),
                pnl=value - cost,
                pnl_pct=(value / cost - 1.0) * 100.0 if cost else 0.0,
                weight=0.0,
                **ind,
            )
        )
    total_usd = sum(r.value_usd for r in rows) + max(cash_usd, 0.0)
    if total_usd <= 0:
        return rows
    return [replace(r, weight=r.value_usd / total_usd) for r in rows]


def build_alerts(
    metrics: list[PositionMetrics],
    earnings: dict[str, date | None],
    vix: float | None,
) -> list[Alert]:
    """All portfolio alerts, most severe first."""
    alerts: list[Alert] = []
    for m in metrics:
        alerts.extend(_position_alerts(m, earnings.get(m.symbol)))
    if vix is not None:
        if vix >= config.VIX_CRIT:
            alerts.append(Alert("crit", "al_vix", {"value": f"{vix:.1f}"}))
        elif vix >= config.VIX_WARN:
            alerts.append(Alert("warn", "al_vix", {"value": f"{vix:.1f}"}))
    order = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(alerts, key=lambda a: order.get(a.severity, 99))


def _position_alerts(m: PositionMetrics, earnings_date: date | None) -> list[Alert]:
    out: list[Alert] = []
    sym = {"symbol": m.symbol}

    if m.pnl_pct <= config.LOSS_CRIT_PCT:
        out.append(Alert("crit", "al_loss", {**sym, "value": f"{m.pnl_pct:.1f}"}))
    elif m.pnl_pct <= config.LOSS_WARN_PCT:
        out.append(Alert("warn", "al_loss", {**sym, "value": f"{m.pnl_pct:.1f}"}))

    if m.change_pct <= config.DAILY_DROP_CRIT:
        out.append(Alert("crit", "al_daily_drop", {**sym, "value": f"{abs(m.change_pct):.1f}"}))
    elif m.change_pct <= config.DAILY_DROP_WARN:
        out.append(Alert("warn", "al_daily_drop", {**sym, "value": f"{abs(m.change_pct):.1f}"}))

    if m.sma_slow is not None and m.price < m.sma_slow:
        out.append(Alert("warn", "al_below_sma_slow", sym))
    elif m.sma_fast is not None and m.price < m.sma_fast:
        out.append(Alert("info", "al_below_sma_fast", sym))

    if m.rsi is not None:
        if m.rsi >= config.RSI_OVERBOUGHT:
            out.append(Alert("info", "al_rsi_over", {**sym, "value": f"{m.rsi:.0f}"}))
        elif m.rsi <= config.RSI_OVERSOLD:
            out.append(Alert("warn", "al_rsi_under", {**sym, "value": f"{m.rsi:.0f}"}))

    if m.atr_stop is not None and m.price > 0:
        dist = (m.price - m.atr_stop) / m.price
        if 0 <= dist <= 0.02:
            out.append(Alert("warn", "al_near_stop", {**sym, "value": f"{m.atr_stop:,.2f}"}))

    if m.weight >= config.CONCENTRATION_WARN:
        out.append(Alert("warn", "al_concentration", {**sym, "value": f"{m.weight * 100:.0f}"}))

    if earnings_date is not None:
        days = (earnings_date - date.today()).days
        if 0 <= days <= config.EARNINGS_SOON_DAYS:
            out.append(Alert("warn", "al_earnings", {**sym, "date": earnings_date.isoformat()}))
    return out


def _indicators_for(hist: pd.DataFrame) -> dict:
    if hist.empty:
        return {"rsi": None, "sma_fast": None, "sma_slow": None, "atr_stop": None}
    close = hist["Close"]
    atr_val = last_value(atr(hist["High"], hist["Low"], close, config.ATR_PERIOD))
    price = last_value(close)
    stop = None
    if atr_val is not None and price is not None:
        stop = max(price - config.ATR_STOP_MULT * atr_val, 0.0)
    return {
        "rsi": last_value(rsi(close, config.RSI_PERIOD)),
        "sma_fast": last_value(sma(close, config.SMA_FAST)),
        "sma_slow": last_value(sma(close, config.SMA_SLOW)),
        "atr_stop": stop,
    }


def portfolio_totals(
    metrics: list[PositionMetrics],
    usdtry: float | None,
    cash: list[CashHolding] | None = None,
) -> dict:
    """Aggregate value / cost / P&L in both currencies plus weighted daily change.

    Cash counts toward total value but never toward profit or loss: it is
    carried at face value on both the value and the cost side.
    """
    balances = cash_totals(cash or [], usdtry)
    invested_try = sum(m.value_try for m in metrics)
    invested_usd = sum(m.value_usd for m in metrics)
    cost_usd = sum(to_usd(m.quantity * m.avg_cost, m.currency, usdtry) for m in metrics)
    cost_try = sum(to_try(m.quantity * m.avg_cost, m.currency, usdtry) for m in metrics)
    daily = sum(m.change_pct * m.weight for m in metrics) if metrics else 0.0
    return {
        "value_try": invested_try + balances["try"],
        "value_usd": invested_usd + balances["usd"],
        "invested_try": invested_try,
        "invested_usd": invested_usd,
        "cash_try": balances["try"],
        "cash_usd": balances["usd"],
        "cash_weight": (
            balances["usd"] / (invested_usd + balances["usd"])
            if invested_usd + balances["usd"] > 0
            else 0.0
        ),
        "cost_try": cost_try + balances["try"],
        "cost_usd": cost_usd + balances["usd"],
        "pnl_usd": invested_usd - cost_usd,
        "pnl_pct": (invested_usd / cost_usd - 1.0) * 100.0 if cost_usd else 0.0,
        "daily_pct": daily,
    }
