from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from portfoy.stage_analysis import (
    StageAnalysis,
    _direction,
    _stage_at,
    build_stage_scan,
    classify_symbol,
    weekly_close,
)

WEEKS = 200


def _weekly_series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2022-01-02", periods=len(values), freq="W")
    return pd.Series(values, index=idx, dtype=float)


def _daily_series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2022-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx, dtype=float)


def _uptrend_daily(days: int = WEEKS * 7, start: float = 100.0, step: float = 0.5) -> pd.Series:
    return _daily_series([start + i * step for i in range(days)])


def _downtrend_daily(days: int = WEEKS * 7, start: float = 300.0, step: float = 0.15) -> pd.Series:
    return _daily_series([start - i * step for i in range(days)])


class TestWeeklyClose:
    def test_resamples_daily_to_weekly(self):
        daily = _daily_series([100.0 + i for i in range(21)])  # 3 weeks of daily bars
        weekly = weekly_close(daily)
        assert len(weekly) < len(daily)
        assert weekly.iloc[-1] == daily.iloc[-1]

    def test_non_datetime_index_returns_empty(self):
        series = pd.Series([1.0, 2.0, 3.0])
        assert weekly_close(series).empty


class TestDirection:
    def test_above_positive_threshold_is_up(self):
        assert _direction(5.0) == "up"

    def test_below_negative_threshold_is_down(self):
        assert _direction(-5.0) == "down"

    def test_within_threshold_is_flat(self):
        assert _direction(0.2) == "flat"
        assert _direction(-0.2) == "flat"


class TestStageAt:
    """Exercises the classification rule directly against hand-built
    close/SMA series -- avoids reverse-engineering a price series that
    happens to produce a particular SMA shape."""

    def test_none_when_not_enough_lookback(self):
        close = _weekly_series([100.0] * 10)
        sma_line = pd.Series([100.0] * 10, index=close.index)
        assert _stage_at(close, sma_line, 2) is None

    def test_rising_sma_and_price_above_is_stage_2(self):
        close = _weekly_series([120.0] * 10)
        sma_line = _weekly_series([100.0, 100.0, 100.0, 100.0, 110.0, 111, 112, 113, 114, 115.0])
        assert _stage_at(close, sma_line, 9) == 2

    def test_falling_sma_and_price_below_is_stage_4(self):
        close = _weekly_series([80.0] * 10)
        sma_line = _weekly_series([120.0, 120, 120, 120, 110, 109, 108, 107, 106, 105.0])
        assert _stage_at(close, sma_line, 9) == 4

    def test_flat_sma_with_rising_context_is_stage_3(self):
        # Flat over the slope lookback, but 20 weeks ago it was much lower --
        # a topping pattern after an advance.
        sma_values = [80.0] * 5 + list(np.linspace(80.0, 150.0, 20)) + [150.0] * 5
        sma_line = _weekly_series(sma_values)
        close = _weekly_series([150.0] * len(sma_values))
        assert _stage_at(close, sma_line, len(sma_values) - 1) == 3

    def test_flat_sma_with_falling_context_is_stage_1(self):
        # Flat over the slope lookback, but 20 weeks ago it was much higher --
        # a base after a decline.
        sma_values = [150.0] * 5 + list(np.linspace(150.0, 80.0, 20)) + [80.0] * 5
        sma_line = _weekly_series(sma_values)
        close = _weekly_series([80.0] * len(sma_values))
        assert _stage_at(close, sma_line, len(sma_values) - 1) == 1

    def test_rising_sma_but_price_dipped_under_is_stage_3(self):
        close = _weekly_series([90.0] * 10)
        sma_line = _weekly_series([80.0, 80, 80, 80, 90, 91, 92, 93, 94, 95.0])
        assert _stage_at(close, sma_line, 9) == 3

    def test_falling_sma_but_price_poked_above_is_stage_1(self):
        close = _weekly_series([110.0] * 10)
        sma_line = _weekly_series([120.0, 120, 120, 120, 110, 109, 108, 107, 106, 105.0])
        assert _stage_at(close, sma_line, 9) == 1


class TestClassifySymbol:
    def test_insufficient_history_returns_none(self):
        daily = _uptrend_daily(days=10 * 7)  # 10 weeks, well short of 34
        assert classify_symbol("AAA", daily) is None

    def test_sustained_uptrend_is_stage_2(self):
        result = classify_symbol("AAA", _uptrend_daily())
        assert result is not None
        assert result.stage == 2
        assert result.trend == "yukselis"
        assert result.technical_alert is False
        assert result.sma30w_slope_pct > 0
        assert result.price_vs_sma_pct > 0
        # A strictly monotonic series never changes stage once classifiable.
        assert result.weeks_in_stage > 1
        assert result.stage_changed is False

    def test_sustained_downtrend_is_stage_4(self):
        result = classify_symbol("AAA", _downtrend_daily())
        assert result is not None
        assert result.stage == 4
        assert result.trend == "dusus"
        assert result.technical_alert is True
        assert result.sma30w_slope_pct < 0
        assert result.price_vs_sma_pct < 0

    def test_relative_strength_tracks_close_vs_flat_benchmark(self):
        benchmark = _daily_series([100.0] * (WEEKS * 7))
        result = classify_symbol("AAA", _uptrend_daily(), benchmark)
        assert result.relative_strength_trend == "yukselis"

    def test_no_benchmark_yields_none_relative_strength(self):
        result = classify_symbol("AAA", _uptrend_daily())
        assert result.relative_strength_trend is None

    def test_summary_mentions_symbol_and_stage(self):
        result = classify_symbol("AAPL", _uptrend_daily())
        assert "AAPL" in result.summary_tr
        assert "Evre 2" in result.summary_tr


class TestBuildStageScan:
    def test_skips_symbols_with_no_history(self):
        out = build_stage_scan(["AAA"], {}, {})
        assert out == []

    def test_skips_symbols_with_insufficient_history(self):
        df = pd.DataFrame({"Close": _uptrend_daily(days=10 * 7)})
        out = build_stage_scan(["AAA"], {"AAA": df}, {})
        assert out == []

    def test_breakdowns_sort_before_advances(self):
        up_df = pd.DataFrame({"Close": _uptrend_daily(start=100.0)})
        down_df = pd.DataFrame({"Close": _downtrend_daily(start=300.0)})
        out = build_stage_scan(["UP", "DOWN"], {"UP": up_df, "DOWN": down_df}, {})
        assert [s.symbol for s in out] == ["DOWN", "UP"]
        assert all(isinstance(s, StageAnalysis) for s in out)

    def test_bist_symbol_uses_try_benchmark(self):
        df = pd.DataFrame({"Close": _uptrend_daily()})
        bench = pd.DataFrame({"Close": _daily_series([100.0] * (WEEKS * 7))})
        out = build_stage_scan(["THYAO.IS"], {"THYAO.IS": df}, {"XU100.IS": bench})
        assert out[0].relative_strength_trend == "yukselis"


@pytest.mark.parametrize("stage", [1, 2, 3, 4])
def test_stage_labels_cover_every_stage(stage):
    from portfoy.stage_analysis import STAGE_LABELS, STAGE_TREND

    assert stage in STAGE_LABELS
    assert stage in STAGE_TREND
