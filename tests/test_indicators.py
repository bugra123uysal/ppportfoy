import numpy as np
import pandas as pd
import pytest

from portfoy.indicators import (
    atr,
    average_daily_range_pct,
    bollinger_bands,
    cci,
    chaikin_money_flow,
    drawdown_from_peak,
    ema,
    last_value,
    money_flow_index,
    on_balance_volume,
    pct_change_last,
    pct_change_over,
    pct_from_52w_high,
    pct_from_52w_low,
    range_pct,
    rsi,
    sma,
    stochastic_momentum_index,
    stochastic_rsi,
    ut_bot_trailing_stop,
    volume_sma,
    weekly_trend_up,
)


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


class TestEma:
    def test_needs_full_window(self, trend_up):
        out = ema(trend_up, 20)
        assert out.iloc[:19].isna().all()
        assert np.isfinite(out.iloc[19])

    def test_lags_behind_price_in_uptrend(self, trend_up):
        out = ema(trend_up, 20)
        assert out.iloc[-1] < trend_up.iloc[-1]


class TestVolumeSma:
    def test_matches_sma(self):
        volume = pd.Series(np.linspace(1000, 2000, 40))
        assert volume_sma(volume, 20).iloc[-1] == pytest.approx(sma(volume, 20).iloc[-1])


class TestBollingerBands:
    def test_zero_volatility_collapses_bands(self):
        close = pd.Series(np.full(30, 100.0))
        upper, mid, lower = bollinger_bands(close, 20, 2.0)
        assert mid.iloc[-1] == pytest.approx(100.0)
        assert upper.iloc[-1] == pytest.approx(100.0)
        assert lower.iloc[-1] == pytest.approx(100.0)

    def test_upper_above_lower_with_volatility(self):
        rng = np.random.default_rng(7)
        close = pd.Series(100 + rng.normal(0, 3, 40))
        upper, mid, lower = bollinger_bands(close, 20, 2.0)
        assert upper.iloc[-1] > mid.iloc[-1] > lower.iloc[-1]


class TestCci:
    def test_flat_series_is_nan(self):
        close = pd.Series(np.full(30, 100.0))
        value = cci(close, close, close, 20).iloc[-1]
        assert pd.isna(value)

    def test_uptrend_is_positive(self, trend_up):
        high, low = trend_up + 1.0, trend_up - 1.0
        value = cci(high, low, trend_up, 20).iloc[-1]
        assert value > 0


class TestStochasticMomentumIndex:
    def test_uptrend_is_positive(self, trend_up):
        high, low = trend_up + 1.0, trend_up - 1.0
        smi, signal = stochastic_momentum_index(high, low, trend_up)
        assert smi.iloc[-1] > 0
        assert np.isfinite(signal.iloc[-1])

    def test_downtrend_is_negative(self):
        down = pd.Series(np.linspace(200, 100, 60))
        high, low = down + 1.0, down - 1.0
        smi, _ = stochastic_momentum_index(high, low, down)
        assert smi.iloc[-1] < 0


class TestStochasticRsi:
    def test_bounded_0_100(self):
        rng = np.random.default_rng(42)
        noisy = pd.Series(100 + rng.normal(0, 2, 200).cumsum())
        k, d = stochastic_rsi(noisy)
        vals = pd.concat([k, d]).dropna()
        assert ((vals >= 0) & (vals <= 100)).all()


class TestUtBotTrailingStop:
    def test_stays_below_close_in_uptrend(self, trend_up):
        high, low = trend_up + 1.0, trend_up - 1.0
        stop = ut_bot_trailing_stop(trend_up, high, low)
        tail = stop.iloc[-10:]
        assert (tail < trend_up.iloc[-10:]).all()


class TestChaikinMoneyFlow:
    def test_positive_when_close_near_high(self):
        n = 40
        low = pd.Series(np.full(n, 100.0))
        high = pd.Series(np.full(n, 110.0))
        close = pd.Series(np.full(n, 109.0))  # near the high every bar
        volume = pd.Series(np.full(n, 1000.0))
        value = chaikin_money_flow(high, low, close, volume, 20).iloc[-1]
        assert value > 0

    def test_negative_when_close_near_low(self):
        n = 40
        low = pd.Series(np.full(n, 100.0))
        high = pd.Series(np.full(n, 110.0))
        close = pd.Series(np.full(n, 101.0))  # near the low every bar
        volume = pd.Series(np.full(n, 1000.0))
        value = chaikin_money_flow(high, low, close, volume, 20).iloc[-1]
        assert value < 0

    def test_nan_when_no_range(self):
        n = 25
        flat = pd.Series(np.full(n, 100.0))
        volume = pd.Series(np.full(n, 1000.0))
        value = chaikin_money_flow(flat, flat, flat, volume, 20).iloc[-1]
        assert pd.isna(value)


class TestMoneyFlowIndex:
    def test_uptrend_is_high(self, trend_up):
        high, low = trend_up + 1.0, trend_up - 1.0
        volume = pd.Series(np.full(len(trend_up), 1000.0))
        value = money_flow_index(high, low, trend_up, volume, 14).iloc[-1]
        assert value > 70

    def test_downtrend_is_low(self):
        down = pd.Series(np.linspace(200, 100, 60))
        high, low = down + 1.0, down - 1.0
        volume = pd.Series(np.full(len(down), 1000.0))
        value = money_flow_index(high, low, down, volume, 14).iloc[-1]
        assert value < 30

    def test_bounded_0_100(self):
        rng = np.random.default_rng(3)
        noisy = pd.Series(100 + rng.normal(0, 2, 200).cumsum())
        high, low = noisy + 1.0, noisy - 1.0
        volume = pd.Series(rng.uniform(500, 1500, 200))
        vals = money_flow_index(high, low, noisy, volume, 14).dropna()
        assert ((vals >= 0) & (vals <= 100)).all()


class TestOnBalanceVolume:
    def test_rises_every_day_in_uptrend(self, trend_up):
        volume = pd.Series(np.full(len(trend_up), 1000.0))
        obv = on_balance_volume(trend_up, volume)
        assert obv.iloc[-1] > obv.iloc[0]
        assert (obv.diff().iloc[1:] >= 0).all()

    def test_falls_every_day_in_downtrend(self):
        down = pd.Series(np.linspace(200, 100, 60))
        volume = pd.Series(np.full(len(down), 1000.0))
        obv = on_balance_volume(down, volume)
        assert obv.iloc[-1] < obv.iloc[0]

    def test_flat_series_stays_zero(self):
        flat = pd.Series(np.full(30, 100.0))
        volume = pd.Series(np.full(30, 1000.0))
        obv = on_balance_volume(flat, volume)
        assert (obv == 0).all()


class TestPctFrom52wHigh:
    def test_at_the_high_is_zero(self):
        close = pd.Series(np.linspace(100.0, 200.0, 260))
        assert pct_from_52w_high(close) == pytest.approx(0.0)

    def test_below_the_high_is_negative(self):
        close = pd.Series([*np.linspace(100.0, 200.0, 259), 180.0])
        value = pct_from_52w_high(close)
        assert value is not None
        assert value < 0
        assert value == pytest.approx((180.0 / 200.0 - 1.0) * 100.0)

    def test_only_looks_within_window(self):
        # An old spike outside the window shouldn't suppress a new high.
        close = pd.Series([500.0, *np.linspace(100.0, 200.0, 259)])
        assert pct_from_52w_high(close, window=259) == pytest.approx(0.0)

    def test_empty_returns_none(self):
        assert pct_from_52w_high(pd.Series(dtype=float)) is None


class TestPctFrom52wLow:
    def test_at_the_low_is_zero(self):
        close = pd.Series(np.linspace(200.0, 100.0, 260))
        assert pct_from_52w_low(close) == pytest.approx(0.0)

    def test_above_the_low_is_positive(self):
        close = pd.Series([*np.linspace(200.0, 100.0, 259), 120.0])
        value = pct_from_52w_low(close)
        assert value is not None
        assert value > 0
        assert value == pytest.approx((120.0 / 100.0 - 1.0) * 100.0)

    def test_empty_returns_none(self):
        assert pct_from_52w_low(pd.Series(dtype=float)) is None


class TestPctChangeOver:
    def test_computes_change_from_n_sessions_ago(self):
        close = pd.Series([100.0, 105.0, 110.0, 121.0])
        assert pct_change_over(close, 2) == pytest.approx((121.0 / 105.0 - 1.0) * 100.0)

    def test_none_on_insufficient_history(self):
        close = pd.Series([100.0, 105.0])
        assert pct_change_over(close, 5) is None

    def test_none_when_reference_price_is_zero(self):
        close = pd.Series([0.0, 105.0, 110.0])
        assert pct_change_over(close, 2) is None


class TestAverageDailyRangePct:
    def test_computes_mean_of_daily_high_low_ratio(self):
        high = pd.Series([110.0] * 20)
        low = pd.Series([100.0] * 20)
        assert average_daily_range_pct(high, low, period=20) == pytest.approx(10.0)

    def test_only_uses_trailing_window(self):
        # A wide-range day outside the window shouldn't drag the average up.
        high = pd.Series([200.0, *([110.0] * 20)])
        low = pd.Series([100.0, *([100.0] * 20)])
        assert average_daily_range_pct(high, low, period=20) == pytest.approx(10.0)

    def test_none_on_insufficient_history(self):
        high = pd.Series([110.0] * 5)
        low = pd.Series([100.0] * 5)
        assert average_daily_range_pct(high, low, period=20) is None


class TestRangePct:
    def test_computes_high_low_span_as_pct_of_last_close(self):
        high = pd.Series([100.0, 105.0, 103.0, 108.0])
        low = pd.Series([95.0, 96.0, 97.0, 99.0])
        close = pd.Series([98.0, 100.0, 101.0, 104.0])
        # span = max(high) - min(low) = 108 - 95 = 13; last close = 104
        assert range_pct(high, low, close, period=4) == pytest.approx(13.0 / 104.0 * 100.0)

    def test_contraction_is_visible_as_a_smaller_recent_window(self):
        high = pd.Series([150.0, 100.0, 101.0, 102.0])
        low = pd.Series([50.0, 99.0, 100.0, 101.0])
        close = pd.Series([100.0, 100.0, 100.5, 101.0])
        wide = range_pct(high, low, close, period=4)
        narrow = range_pct(high, low, close, period=2)
        assert narrow < wide

    def test_none_on_insufficient_history(self):
        high = pd.Series([100.0, 105.0])
        low = pd.Series([95.0, 96.0])
        close = pd.Series([98.0, 100.0])
        assert range_pct(high, low, close, period=10) is None

    def test_none_on_empty_close(self):
        empty = pd.Series(dtype=float)
        assert range_pct(empty, empty, empty, 5) is None


class TestWeeklyTrendUp:
    def _dated_close(self, values: np.ndarray) -> pd.Series:
        index = pd.date_range("2024-01-01", periods=len(values), freq="B")
        return pd.Series(values, index=index)

    def test_none_without_datetime_index(self):
        close = pd.Series(np.linspace(100, 200, 60))
        assert weekly_trend_up(close, 10) is None

    def test_true_on_weekly_uptrend(self):
        close = self._dated_close(np.linspace(100.0, 300.0, 400))
        assert weekly_trend_up(close, 10) is True

    def test_false_on_weekly_downtrend(self):
        close = self._dated_close(np.linspace(300.0, 100.0, 400))
        assert weekly_trend_up(close, 10) is False

    def test_none_on_short_history(self):
        close = self._dated_close(np.linspace(100.0, 110.0, 30))
        assert weekly_trend_up(close, 10) is None
