import numpy as np
import pandas as pd
import pytest

from portfoy.indicators import atr, drawdown_from_peak, last_value, pct_change_last, rsi, sma


@pytest.fixture
def trend_up():
    return pd.Series(np.linspace(100, 200, 60))


class TestSma:
    def test_needs_full_window(self, trend_up):
        out = sma(trend_up, 20)
        assert out.iloc[:19].isna().all()
        assert out.iloc[19] == pytest.approx(trend_up.iloc[:20].mean())


class TestRsi:
    def test_uptrend_is_high(self, trend_up):
        value = rsi(trend_up, 14).iloc[-1]
        assert value > 70

    def test_downtrend_is_low(self):
        down = pd.Series(np.linspace(200, 100, 60))
        assert rsi(down, 14).iloc[-1] < 30

    def test_bounded_0_100(self):
        rng = np.random.default_rng(42)
        noisy = pd.Series(100 + rng.normal(0, 2, 200).cumsum())
        vals = rsi(noisy, 14).dropna()
        assert ((vals >= 0) & (vals <= 100)).all()


class TestAtr:
    def test_positive_and_reasonable(self):
        n = 50
        close = pd.Series(np.full(n, 100.0))
        high = close + 2.0
        low = close - 2.0
        val = atr(high, low, close, 14).iloc[-1]
        assert val == pytest.approx(4.0, rel=0.1)


class TestHelpers:
    def test_pct_change_last(self):
        assert pct_change_last(pd.Series([100.0, 110.0])) == pytest.approx(10.0)

    def test_pct_change_short_series(self):
        assert pct_change_last(pd.Series([100.0])) == 0.0
        assert pct_change_last(pd.Series(dtype=float)) == 0.0

    def test_drawdown(self):
        series = pd.Series([100.0, 150.0, 120.0])
        assert drawdown_from_peak(series) == pytest.approx(-20.0)

    def test_last_value_empty(self):
        assert last_value(pd.Series(dtype=float)) is None
