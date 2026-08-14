import dataclasses
import json

import numpy as np
import pandas as pd
import pytest

from portfoy import config
from portfoy.fibonacci import FibLevel, FibLevels, build_levels
from portfoy.serialize import dumps

SWING_LOW = 100.0
SWING_HIGH = 200.0
SPAN = SWING_HIGH - SWING_LOW


def _swing_df(
    n: int = 40,
    low_idx: int = 5,
    high_idx: int = 30,
    swing_low: float = SWING_LOW,
    swing_high: float = SWING_HIGH,
    last_close: float | None = None,
) -> pd.DataFrame:
    """A window with exactly one extreme high and one extreme low, at known
    dates -- everything else sits comfortably inside the range so max/min are
    unambiguous."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    mid = (swing_low + swing_high) / 2.0
    high = np.full(n, mid + 5.0)
    low = np.full(n, mid - 5.0)
    close = np.full(n, mid)
    high[high_idx] = swing_high
    low[low_idx] = swing_low
    if last_close is not None:
        close[-1] = last_close
    return pd.DataFrame({"High": high, "Low": low, "Close": close}, index=idx)


class TestUptrendSwing:
    """Low happened before the high -> retracement measured down from the
    high toward the low."""

    def test_direction_is_yukselis(self):
        result = build_levels(_swing_df(low_idx=5, high_idx=30), 40)
        assert result is not None
        assert result.direction == "yukselis"
        assert result.swing_high == pytest.approx(SWING_HIGH)
        assert result.swing_low == pytest.approx(SWING_LOW)

    def test_swing_dates_match_the_extreme_bars(self):
        df = _swing_df(low_idx=5, high_idx=30)
        result = build_levels(df, 40)
        assert result.swing_low_date == df.index[5].date().isoformat()
        assert result.swing_high_date == df.index[30].date().isoformat()

    def test_retracement_prices_match_formula_and_descend_below_high(self):
        result = build_levels(_swing_df(low_idx=5, high_idx=30), 40)
        retracements = [lvl for lvl in result.levels if lvl.kind == "retracement"]
        assert [lvl.ratio for lvl in retracements] == list(config.FIB_RETRACEMENT_RATIOS)
        prices = [lvl.price for lvl in retracements]
        expected = [SWING_HIGH - SPAN * r for r in config.FIB_RETRACEMENT_RATIOS]
        assert prices == pytest.approx(expected)
        # Strictly descending as the ratio grows -- deeper retracement = lower price.
        assert all(a > b for a, b in zip(prices, prices[1:]))  # noqa: B905 -- pairwise, uneven by design
        assert all(p < SWING_HIGH for p in prices)

    def test_extension_prices_match_formula(self):
        result = build_levels(_swing_df(low_idx=5, high_idx=30), 40)
        extensions = [lvl for lvl in result.levels if lvl.kind == "extension"]
        assert [lvl.ratio for lvl in extensions] == list(config.FIB_EXTENSION_RATIOS)
        prices = [lvl.price for lvl in extensions]
        expected = [SWING_HIGH + SPAN * (r - 1) for r in config.FIB_EXTENSION_RATIOS]
        assert prices == pytest.approx(expected)
        assert all(p > SWING_HIGH for p in prices)


class TestDowntrendSwing:
    """High happened before the low -> retracement measured up from the low
    toward the high; formulas invert relative to the uptrend case."""

    def test_direction_is_dusus(self):
        result = build_levels(_swing_df(low_idx=30, high_idx=5), 40)
        assert result is not None
        assert result.direction == "dusus"

    def test_retracement_prices_match_formula_and_ascend_above_low(self):
        result = build_levels(_swing_df(low_idx=30, high_idx=5), 40)
        retracements = [lvl for lvl in result.levels if lvl.kind == "retracement"]
        prices = [lvl.price for lvl in retracements]
        expected = [SWING_LOW + SPAN * r for r in config.FIB_RETRACEMENT_RATIOS]
        assert prices == pytest.approx(expected)
        # Strictly ascending -- inverse of the uptrend case.
        assert all(a < b for a, b in zip(prices, prices[1:]))  # noqa: B905 -- pairwise, uneven by design
        assert all(p > SWING_LOW for p in prices)

    def test_extension_prices_match_formula(self):
        result = build_levels(_swing_df(low_idx=30, high_idx=5), 40)
        extensions = [lvl for lvl in result.levels if lvl.kind == "extension"]
        prices = [lvl.price for lvl in extensions]
        expected = [SWING_LOW - SPAN * (r - 1) for r in config.FIB_EXTENSION_RATIOS]
        assert prices == pytest.approx(expected)
        assert all(p < SWING_LOW for p in prices)


class TestNearestLevel:
    def test_nearest_level_is_the_closest_by_price(self):
        # 0.382 retracement in the uptrend case lands exactly at 161.8.
        df = _swing_df(low_idx=5, high_idx=30, last_close=161.8)
        result = build_levels(df, 40)
        assert result.nearest_ratio == pytest.approx(0.382)
        assert result.nearest_price == pytest.approx(161.8)
        assert result.pct_to_nearest == pytest.approx(0.0, abs=1e-9)

    def test_pct_to_nearest_is_signed_distance_from_last_close(self):
        # 155.0 sits closest to the 0.5 retracement (150.0), a known +3.333%.
        df = _swing_df(low_idx=5, high_idx=30, last_close=155.0)
        result = build_levels(df, 40)
        assert result.nearest_ratio == pytest.approx(0.5)
        assert result.pct_to_nearest == pytest.approx(100.0 / 30.0, rel=1e-6)

    def test_negative_pct_when_last_close_is_below_nearest_level(self):
        df = _swing_df(low_idx=5, high_idx=30, last_close=135.0)
        result = build_levels(df, 40)
        assert result.nearest_ratio == pytest.approx(0.618)  # 138.2
        assert result.pct_to_nearest < 0


class TestAtLevel:
    """at_level gates whether the nearest level is actually within
    config.FIB_NEAR_LEVEL_PCT -- "closest of the list" isn't the same claim
    as "price is basically sitting on this level"."""

    def test_true_when_price_sits_exactly_on_a_level(self):
        df = _swing_df(low_idx=5, high_idx=30, last_close=161.8)  # 0.382 exactly
        result = build_levels(df, 40)
        assert result.at_level is True

    def test_true_when_within_the_configured_tolerance(self):
        # 0.5 retracement is 150.0; nudge close price just inside FIB_NEAR_LEVEL_PCT.
        nudged = 150.0 * (1 + (config.FIB_NEAR_LEVEL_PCT / 100.0) * 0.5)
        df = _swing_df(low_idx=5, high_idx=30, last_close=nudged)
        result = build_levels(df, 40)
        assert result.nearest_ratio == pytest.approx(0.5)
        assert result.at_level is True

    def test_false_when_far_from_every_level(self):
        # 155.0 sits +3.33% from the nearest (0.5 @ 150.0) -- well past tolerance.
        df = _swing_df(low_idx=5, high_idx=30, last_close=155.0)
        result = build_levels(df, 40)
        assert abs(result.pct_to_nearest) > config.FIB_NEAR_LEVEL_PCT
        assert result.at_level is False


class TestZoneLabel:
    def test_price_between_two_retracement_levels(self):
        # Between the 0.382 (161.8) and 0.5 (150.0) uptrend levels.
        df = _swing_df(low_idx=5, high_idx=30, last_close=155.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0.382 - 0.5 arası"

    def test_price_above_all_retracement_levels_uses_edge_label(self):
        df = _swing_df(low_idx=5, high_idx=30, last_close=199.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0 altında"

    def test_price_below_all_retracement_levels_uses_edge_label(self):
        df = _swing_df(low_idx=5, high_idx=30, last_close=101.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0.786 üzerinde"

    def test_downtrend_price_between_two_retracement_levels(self):
        # Retracements ascend from the low in "dusus" (0.5 -> 150.0,
        # 0.618 -> 161.8), the inverse ordering from the uptrend case, so
        # 155.0 brackets a different ratio pair here even at the same price.
        df = _swing_df(low_idx=30, high_idx=5, last_close=155.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0.5 - 0.618 arası"

    def test_downtrend_price_above_all_retracement_levels_uses_edge_label(self):
        # Least pulled-back (closest to the low) -> "0 altında", same as uptrend.
        df = _swing_df(low_idx=30, high_idx=5, last_close=101.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0 altında"

    def test_downtrend_price_below_all_retracement_levels_uses_edge_label(self):
        # Most pulled-back (closest to the high) -> "0.786 üzerinde".
        df = _swing_df(low_idx=30, high_idx=5, last_close=199.0)
        result = build_levels(df, 40)
        assert result.zone_label == "0.786 üzerinde"


class TestRatiosMatchConfig:
    def test_output_ratios_match_config_constants(self):
        result = build_levels(_swing_df(), 40)
        retracement_ratios = [lvl.ratio for lvl in result.levels if lvl.kind == "retracement"]
        extension_ratios = [lvl.ratio for lvl in result.levels if lvl.kind == "extension"]
        assert retracement_ratios == list(config.FIB_RETRACEMENT_RATIOS)
        assert extension_ratios == list(config.FIB_EXTENSION_RATIOS)


class TestEdgeCases:
    def test_none_on_zero_range_window(self):
        df = _swing_df(swing_low=150.0, swing_high=150.0)
        # Flatten everything to the same price so high == low across the board.
        df["High"] = 150.0
        df["Low"] = 150.0
        assert build_levels(df, 40) is None

    def test_none_on_too_short_dataframe(self):
        df = _swing_df(n=5, low_idx=1, high_idx=3)
        assert build_levels(df, 40) is None

    def test_none_on_empty_dataframe(self):
        assert build_levels(pd.DataFrame(), 40) is None

    def test_none_when_high_low_are_all_nan_in_window(self):
        df = _swing_df()
        df["High"] = np.nan
        df["Low"] = np.nan
        assert build_levels(df, 40) is None

    def test_lookback_window_is_respected(self):
        # Swing points inside the trailing 40-day window (rows 160-199)...
        df = _swing_df(n=200, low_idx=165, high_idx=190)
        # ...plus an even more extreme low far outside it, which must be ignored.
        df.iloc[0, df.columns.get_loc("Low")] = 1.0
        result = build_levels(df, 40)
        assert result is not None
        assert result.swing_low == pytest.approx(SWING_LOW)

    def test_lookback_days_is_recorded_on_the_result(self):
        result = build_levels(_swing_df(), 40)
        assert result.lookback_days == 40


class TestDataclassShape:
    def test_fib_level_and_fib_levels_are_frozen_dataclasses(self):
        assert dataclasses.is_dataclass(FibLevel)
        assert dataclasses.is_dataclass(FibLevels)
        assert FibLevel.__dataclass_params__.frozen
        assert FibLevels.__dataclass_params__.frozen
        # Neither should be a NamedTuple -- see serialize.py's module docstring
        # for the exact historical bug this guards against.
        assert not issubclass(FibLevel, tuple)
        assert not issubclass(FibLevels, tuple)


class TestSerializationRoundTrip:
    def test_serializes_as_a_keyed_object_not_a_positional_array(self):
        result = build_levels(_swing_df(low_idx=5, high_idx=30, last_close=155.0), 40)
        decoded = json.loads(dumps(result))
        assert isinstance(decoded, dict)
        assert decoded["direction"] == "yukselis"
        assert decoded["swing_high"] == pytest.approx(SWING_HIGH)
        assert isinstance(decoded["at_level"], bool)
        assert isinstance(decoded["levels"], list)
        assert isinstance(decoded["levels"][0], dict)
        assert "ratio" in decoded["levels"][0]
        assert "price" in decoded["levels"][0]
        assert "kind" in decoded["levels"][0]
