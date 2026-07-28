import pandas as pd
import pytest

from portfoy.options import (
    OptionActivity,
    aggregate_chain,
    build_activity,
    pcr_mood,
    rank_by_volume,
)


def _chain(volumes, strikes=None, oi=None) -> pd.DataFrame:
    n = len(volumes)
    return pd.DataFrame(
        {
            "strike": strikes if strikes is not None else [100.0 + i for i in range(n)],
            "lastPrice": [1.5] * n,
            "volume": volumes,
            "openInterest": oi if oi is not None else [10] * n,
            "impliedVolatility": [0.45] * n,
        }
    )


def _activity(symbol="AAA", call=100, put=50) -> OptionActivity:
    return OptionActivity(symbol=symbol, expiry="2026-07-24", call_volume=call,
                          put_volume=put, call_oi=0, put_oi=0)


class TestAggregateChain:
    def test_sums_volumes(self):
        summary = aggregate_chain(_chain([100, 200]), _chain([50, 25]))
        assert summary["call_volume"] == 300
        assert summary["put_volume"] == 75

    def test_sums_open_interest(self):
        summary = aggregate_chain(_chain([1], oi=[500]), _chain([1], oi=[300]))
        assert summary["call_oi"] == 500
        assert summary["put_oi"] == 300

    def test_nan_volumes_treated_as_zero(self):
        summary = aggregate_chain(_chain([100, float("nan")]), _chain([float("nan")]))
        assert summary["call_volume"] == 100
        assert summary["put_volume"] == 0

    def test_empty_frames(self):
        summary = aggregate_chain(pd.DataFrame(), pd.DataFrame())
        assert summary["call_volume"] == 0
        assert summary["top_contracts"] == []

    def test_top_contracts_sorted_by_volume(self):
        summary = aggregate_chain(_chain([10, 900]), _chain([500]), top_n=2)
        top = summary["top_contracts"]
        assert len(top) == 2
        assert top[0]["volume"] == 900 and top[0]["type"] == "CALL"
        assert top[1]["volume"] == 500 and top[1]["type"] == "PUT"

    def test_top_n_respected(self):
        summary = aggregate_chain(_chain([1, 2, 3, 4]), _chain([5, 6]), top_n=3)
        assert len(summary["top_contracts"]) == 3


class TestBuildActivity:
    def test_round_trip(self):
        summary = aggregate_chain(_chain([100]), _chain([40]))
        activity = build_activity("NVDA", "2026-07-24", summary)
        assert activity.symbol == "NVDA"
        assert activity.total_volume == 140
        assert activity.put_call_ratio == pytest.approx(0.4)

    def test_missing_keys_default_to_zero(self):
        activity = build_activity("X", "2026-07-24", {})
        assert activity.total_volume == 0
        assert activity.put_call_ratio is None


class TestPutCallRatio:
    def test_ratio(self):
        assert _activity(call=200, put=100).put_call_ratio == pytest.approx(0.5)

    def test_zero_calls_is_none(self):
        assert _activity(call=0, put=100).put_call_ratio is None


class TestRankByVolume:
    def test_busiest_first(self):
        ranked = rank_by_volume([_activity("A", 10, 5), _activity("B", 500, 400)])
        assert [a.symbol for a in ranked] == ["B", "A"]

    def test_zero_volume_dropped(self):
        ranked = rank_by_volume([_activity("A", 0, 0), _activity("B", 1, 0)])
        assert [a.symbol for a in ranked] == ["B"]

    def test_empty(self):
        assert rank_by_volume([]) == []


class TestPcrMood:
    @pytest.mark.parametrize(
        ("ratio", "expected"),
        [(None, "neutral"), (1.2, "bearish"), (1.0, "bearish"),
         (0.5, "bullish"), (0.7, "bullish"), (0.85, "neutral")],
    )
    def test_moods(self, ratio, expected):
        assert pcr_mood(ratio) == expected
