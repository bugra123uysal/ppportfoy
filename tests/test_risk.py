from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from portfoy.data import Quote
from portfoy.risk import build_alerts, compute_metrics, portfolio_totals
from portfoy.storage import make_position


def _hist(n=250, start=100.0, end=100.0):
    close = pd.Series(np.linspace(start, end, n))
    return pd.DataFrame(
        {"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close}
    )


def _metrics(price=100.0, avg_cost=100.0, change_pct=0.0, hist=None, symbol="AAPL"):
    positions = [make_position(symbol, 10, avg_cost)]
    quotes = {symbol: Quote(symbol, price, price / (1 + change_pct / 100), change_pct)}
    histories = {symbol: hist if hist is not None else _hist()}
    return compute_metrics(positions, quotes, histories, usdtry=40.0)


class TestComputeMetrics:
    def test_basic_pnl(self):
        m = _metrics(price=120.0, avg_cost=100.0)[0]
        assert m.pnl == pytest.approx(200.0)
        assert m.pnl_pct == pytest.approx(20.0)
        assert m.value_usd == pytest.approx(1200.0)
        assert m.value_try == pytest.approx(48000.0)

    def test_try_position_converts(self):
        positions = [make_position("THYAO.IS", 100, 250.0)]
        quotes = {"THYAO.IS": Quote("THYAO.IS", 300.0, 295.0, 1.7)}
        m = compute_metrics(positions, quotes, {}, usdtry=40.0)[0]
        assert m.value_try == pytest.approx(30000.0)
        assert m.value_usd == pytest.approx(750.0)

    def test_missing_quote_skipped(self):
        positions = [make_position("AAPL", 10, 100.0)]
        assert compute_metrics(positions, {}, {}, 40.0) == []

    def test_weights_sum_to_one(self):
        positions = [make_position("AAPL", 10, 100.0), make_position("MSFT", 5, 200.0)]
        quotes = {
            "AAPL": Quote("AAPL", 100.0, 100.0, 0.0),
            "MSFT": Quote("MSFT", 200.0, 200.0, 0.0),
        }
        metrics = compute_metrics(positions, quotes, {}, 40.0)
        assert sum(m.weight for m in metrics) == pytest.approx(1.0)


class TestAlerts:
    def test_big_loss_is_critical(self):
        metrics = _metrics(price=75.0, avg_cost=100.0)
        alerts = build_alerts(metrics, {}, vix=None)
        assert any(a.key == "al_loss" and a.severity == "crit" for a in alerts)

    def test_daily_drop_warns(self):
        metrics = _metrics(change_pct=-5.0)
        alerts = build_alerts(metrics, {}, vix=None)
        assert any(a.key == "al_daily_drop" for a in alerts)

    def test_below_sma200_warns(self):
        hist = _hist(start=200.0, end=100.0)  # falling: price under long averages
        metrics = _metrics(price=100.0, hist=hist)
        alerts = build_alerts(metrics, {}, vix=None)
        assert any(a.key == "al_below_sma_slow" for a in alerts)

    def test_earnings_soon(self):
        metrics = _metrics()
        soon = date.today() + timedelta(days=3)
        alerts = build_alerts(metrics, {"AAPL": soon}, vix=None)
        assert any(a.key == "al_earnings" for a in alerts)

    def test_vix_levels(self):
        metrics = _metrics()
        crit = build_alerts(metrics, {}, vix=35.0)
        warn = build_alerts(metrics, {}, vix=27.0)
        calm = build_alerts(metrics, {}, vix=15.0)
        assert any(a.key == "al_vix" and a.severity == "crit" for a in crit)
        assert any(a.key == "al_vix" and a.severity == "warn" for a in warn)
        assert not any(a.key == "al_vix" for a in calm)

    def test_concentration_single_position(self):
        alerts = build_alerts(_metrics(), {}, vix=None)
        assert any(a.key == "al_concentration" for a in alerts)

    def test_sorted_crit_first(self):
        metrics = _metrics(price=70.0, avg_cost=100.0, change_pct=-5.0)
        alerts = build_alerts(metrics, {}, vix=27.0)
        severities = [a.severity for a in alerts]
        assert severities == sorted(severities, key=("crit", "warn", "info").index)


class TestTotals:
    def test_empty(self):
        totals = portfolio_totals([], 40.0)
        assert totals["value_usd"] == 0.0
        assert totals["pnl_pct"] == 0.0

    def test_pnl_pct(self):
        metrics = _metrics(price=110.0, avg_cost=100.0)
        totals = portfolio_totals(metrics, 40.0)
        assert totals["pnl_pct"] == pytest.approx(10.0)
        assert totals["daily_pct"] == pytest.approx(0.0)
