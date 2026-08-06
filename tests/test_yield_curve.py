import pandas as pd
import pytest

from portfoy.yield_curve import build_yield_curve_snapshot, credit_spread_proxy_change


class TestCreditSpreadProxyChange:
    def test_hy_underperforming_is_negative(self):
        index = pd.date_range("2025-01-01", periods=30, freq="B")
        hy = pd.Series([100.0] * 10 + [90.0] * 20, index=index)   # HY drops
        ig = pd.Series([100.0] * 30, index=index)                  # IG flat
        value = credit_spread_proxy_change(hy, ig, lookback=20)
        assert value is not None
        assert value < 0

    def test_hy_outperforming_is_positive(self):
        index = pd.date_range("2025-01-01", periods=30, freq="B")
        hy = pd.Series([100.0] * 10 + [110.0] * 20, index=index)
        ig = pd.Series([100.0] * 30, index=index)
        value = credit_spread_proxy_change(hy, ig, lookback=20)
        assert value is not None
        assert value > 0

    def test_too_short_returns_none(self):
        index = pd.date_range("2025-01-01", periods=5, freq="B")
        hy = pd.Series([100.0] * 5, index=index)
        ig = pd.Series([100.0] * 5, index=index)
        assert credit_spread_proxy_change(hy, ig, lookback=20) is None

    def test_empty_returns_none(self):
        empty = pd.Series(dtype=float)
        assert credit_spread_proxy_change(empty, empty, lookback=20) is None


class TestBuildYieldCurveSnapshot:
    def test_normal_curve_not_inverted(self):
        snap = build_yield_curve_snapshot(yield_10y=4.5, yield_3m=4.0, credit_change_pct=1.0)
        assert snap.spread_10y_3m == pytest.approx(0.5)
        assert snap.inverted is False
        assert snap.credit_stress is False

    def test_inverted_curve(self):
        snap = build_yield_curve_snapshot(yield_10y=4.0, yield_3m=5.0, credit_change_pct=None)
        assert snap.spread_10y_3m == pytest.approx(-1.0)
        assert snap.inverted is True

    def test_credit_stress_flag(self):
        snap = build_yield_curve_snapshot(yield_10y=4.5, yield_3m=4.0, credit_change_pct=-5.0)
        assert snap.credit_stress is True

    def test_missing_yields_no_spread(self):
        snap = build_yield_curve_snapshot(yield_10y=None, yield_3m=4.0, credit_change_pct=None)
        assert snap.spread_10y_3m is None
        assert snap.inverted is False
