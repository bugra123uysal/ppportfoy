import numpy as np
import pandas as pd
import pytest

from portfoy.rotation import (
    IMPROVING,
    LAGGING,
    LEADING,
    WEAKENING,
    build_rotation,
    build_sector_leaders,
    classify,
    cross_normalize,
    is_clockwise,
    raw_rrg_frames,
    rrg_frames,
)

WEEKS = 160


def _closes(**series: np.ndarray) -> pd.DataFrame:
    index = pd.date_range("2023-01-01", periods=WEEKS, freq="W")
    return pd.DataFrame(series, index=index)


def _sector_frame() -> pd.DataFrame:
    """Benchmark plus a strong, a flat and two weak sectors."""
    rng = np.random.default_rng(7)
    noise = lambda scale: rng.normal(0, scale, WEEKS)  # noqa: E731
    return _closes(
        SPY=np.linspace(100.0, 130.0, WEEKS),
        XLK=np.linspace(100.0, 190.0, WEEKS) + noise(1),
        XLF=np.linspace(100.0, 131.0, WEEKS) + noise(1),
        XLU=np.linspace(100.0, 95.0, WEEKS) + noise(1),
        XLP=np.linspace(100.0, 108.0, WEEKS) + noise(1),
    )


class TestClassify:
    @pytest.mark.parametrize(
        ("ratio", "momentum", "expected"),
        [
            (102.0, 101.0, LEADING),
            (102.0, 98.0, WEAKENING),
            (98.0, 98.0, LAGGING),
            (98.0, 102.0, IMPROVING),
            (100.0, 100.0, LEADING),  # boundary belongs to leading
        ],
    )
    def test_quadrants(self, ratio, momentum, expected):
        assert classify(ratio, momentum) == expected


class TestIsClockwise:
    def test_normal_cycle_steps(self):
        assert is_clockwise(IMPROVING, LEADING)
        assert is_clockwise(LEADING, WEAKENING)
        assert is_clockwise(WEAKENING, LAGGING)
        assert is_clockwise(LAGGING, IMPROVING)

    def test_staying_put_counts_as_normal(self):
        assert is_clockwise(LEADING, LEADING)

    def test_backwards_move_is_unusual(self):
        assert not is_clockwise(LEADING, IMPROVING)
        assert not is_clockwise(LAGGING, WEAKENING)


class TestCrossNormalize:
    def test_centres_on_100(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0]})
        result = cross_normalize(frame)
        assert result.mean(axis=1).iloc[0] == pytest.approx(100.0)

    def test_preserves_ordering(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0]})
        row = cross_normalize(frame).iloc[0]
        assert row["a"] < row["b"] < row["c"]

    def test_identical_values_collapse_to_100(self):
        frame = pd.DataFrame({"a": [100.0], "b": [100.0], "c": [100.0]})
        assert cross_normalize(frame).iloc[0].eq(100.0).all()

    def test_empty_frame_passthrough(self):
        assert cross_normalize(pd.DataFrame()).empty

    def test_reference_columns_define_the_scale(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0], "wild": [900.0]})
        reference = ["a", "b", "c"]
        scored = cross_normalize(frame, reference)
        baseline = cross_normalize(frame[reference], reference)
        # The outlier must not move where a/b/c plot.
        for col in reference:
            assert scored[col].iloc[0] == pytest.approx(baseline[col].iloc[0])

    def test_non_reference_symbol_still_scored(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0], "wild": [900.0]})
        scored = cross_normalize(frame, ["a", "b", "c"])
        assert scored["wild"].iloc[0] > scored["c"].iloc[0]

    def test_outlier_clipped_to_bound(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0], "wild": [9e6]})
        scored = cross_normalize(frame, ["a", "b", "c"], clip=6.0)
        assert scored["wild"].iloc[0] == pytest.approx(106.0)

    def test_reference_symbols_untouched_by_clipping(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0], "wild": [9e6]})
        clipped = cross_normalize(frame, ["a", "b", "c"], clip=6.0)
        generous = cross_normalize(frame, ["a", "b", "c"], clip=1e9)
        for col in ("a", "b", "c"):
            assert clipped[col].iloc[0] == pytest.approx(generous[col].iloc[0])

    def test_too_few_reference_columns_falls_back_to_all(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0]})
        assert cross_normalize(frame, ["a"]).equals(cross_normalize(frame))

    def test_unknown_reference_columns_ignored(self):
        frame = pd.DataFrame({"a": [90.0], "b": [100.0], "c": [110.0]})
        assert cross_normalize(frame, ["x", "y", "z"]).equals(cross_normalize(frame))


class TestRawFrames:
    def test_outperformer_above_100(self):
        strength, _ = raw_rrg_frames(_sector_frame())
        assert strength["XLK"].dropna().iloc[-1] > 100.0

    def test_underperformer_below_100(self):
        strength, _ = raw_rrg_frames(_sector_frame())
        assert strength["XLU"].dropna().iloc[-1] < 100.0

    def test_benchmark_excluded(self):
        strength, _ = raw_rrg_frames(_sector_frame())
        assert "SPY" not in strength.columns

    def test_missing_benchmark_returns_empty(self):
        strength, momentum = raw_rrg_frames(_sector_frame(), benchmark="QQQ")
        assert strength.empty and momentum.empty

    def test_too_few_peers_returns_empty(self):
        frame = _closes(SPY=np.linspace(100, 130, WEEKS), XLK=np.linspace(100, 190, WEEKS))
        strength, _ = raw_rrg_frames(frame)
        assert strength.empty


class TestRrgFrames:
    def test_leader_right_of_laggard(self):
        ratio, _ = rrg_frames(_sector_frame())
        assert ratio["XLK"].iloc[-1] > ratio["XLU"].iloc[-1]

    def test_leader_above_100(self):
        ratio, _ = rrg_frames(_sector_frame())
        assert ratio["XLK"].iloc[-1] > 100.0


class TestBuildRotation:
    def test_benchmark_excluded_from_results(self):
        points = build_rotation(_sector_frame(), {})
        assert {p.symbol for p in points} == {"XLK", "XLF", "XLU", "XLP"}

    def test_labels_applied(self):
        points = build_rotation(_sector_frame(), {"XLK": ("Teknoloji", "Technology")})
        tech = next(p for p in points if p.symbol == "XLK")
        assert tech.label("tr") == "Teknoloji"
        assert tech.label("en") == "Technology"

    def test_unlabelled_symbol_falls_back_to_ticker(self):
        points = build_rotation(_sector_frame(), {})
        assert next(p for p in points if p.symbol == "XLU").label("tr") == "XLU"

    def test_outperformer_leads_underperformer(self):
        points = build_rotation(_sector_frame(), {})
        tech = next(p for p in points if p.symbol == "XLK")
        utils = next(p for p in points if p.symbol == "XLU")
        assert tech.x > utils.x

    def test_strongest_sector_is_in_leading_quadrant(self):
        points = build_rotation(_sector_frame(), {})
        assert next(p for p in points if p.symbol == "XLK").quadrant in (LEADING, WEAKENING)

    def test_sorted_by_strength(self):
        points = build_rotation(_sector_frame(), {})
        assert [p.x for p in points] == sorted([p.x for p in points], reverse=True)

    def test_tail_length_respected(self):
        points = build_rotation(_sector_frame(), {}, tail=6)
        assert all(len(p.tail_x) == 6 and len(p.tail_y) == 6 for p in points)

    def test_tail_always_has_two_points_for_arrow(self):
        points = build_rotation(_sector_frame(), {}, tail=1)
        assert all(len(p.tail_x) >= 2 for p in points)

    def test_has_moved_flag(self):
        points = build_rotation(_sector_frame(), {})
        for point in points:
            assert point.has_moved == (point.quadrant != point.prev_quadrant)

    def test_missing_benchmark_returns_empty(self):
        assert build_rotation(_sector_frame(), {}, benchmark="QQQ") == []

    def test_short_history_skipped(self):
        assert build_rotation(_sector_frame().head(12), {}) == []

    def test_empty_frame_returns_empty(self):
        assert build_rotation(pd.DataFrame(), {}) == []

    def test_overlaying_a_volatile_symbol_does_not_move_sectors(self):
        sectors = ["XLK", "XLF", "XLU", "XLP"]
        base = build_rotation(_sector_frame(), {}, reference=sectors)
        rng = np.random.default_rng(3)
        with_extra = _sector_frame()
        with_extra["WILD"] = np.linspace(10.0, 900.0, WEEKS) + rng.normal(0, 40, WEEKS)
        overlaid = build_rotation(with_extra, {}, reference=sectors)

        base_by_symbol = {p.symbol: p for p in base}
        for point in overlaid:
            if point.symbol == "WILD":
                continue
            assert point.x == pytest.approx(base_by_symbol[point.symbol].x)
            assert point.quadrant == base_by_symbol[point.symbol].quadrant

    def test_performance_fields_populated(self):
        points = build_rotation(_sector_frame(), {})
        tech = next(p for p in points if p.symbol == "XLK")
        utils = next(p for p in points if p.symbol == "XLU")
        assert tech.perf_3m > 0
        assert utils.perf_3m < tech.perf_3m


def _stock_frame() -> pd.DataFrame:
    """A strong, a flat and a weak stock, plus an unrelated symbol not in any pool.

    Deliberately noise-free (unlike _sector_frame): the ranking tests below
    assert an exact strongest-first order, which trailing-4-week noise could
    flip for closely-spaced trends.
    """
    return _closes(
        HOT=np.linspace(100.0, 200.0, WEEKS),
        MEH=np.linspace(100.0, 105.0, WEEKS),
        COLD=np.linspace(100.0, 60.0, WEEKS),
        OTHER=np.linspace(100.0, 500.0, WEEKS),
    )


class TestBuildSectorLeaders:
    def test_ranks_by_1m_return_strongest_first(self):
        pool = {"SECT": ("HOT", "MEH", "COLD")}
        leaders = build_sector_leaders(_stock_frame(), pool, top_n=5)
        symbols = [leader.symbol for leader in leaders["SECT"]]
        assert symbols == ["HOT", "MEH", "COLD"]

    def test_respects_top_n(self):
        pool = {"SECT": ("HOT", "MEH", "COLD")}
        leaders = build_sector_leaders(_stock_frame(), pool, top_n=2)
        assert len(leaders["SECT"]) == 2

    def test_symbol_missing_from_closes_is_skipped(self):
        pool = {"SECT": ("HOT", "GHOST")}
        leaders = build_sector_leaders(_stock_frame(), pool, top_n=5)
        assert [leader.symbol for leader in leaders["SECT"]] == ["HOT"]

    def test_symbol_outside_the_pool_is_ignored(self):
        pool = {"SECT": ("HOT", "MEH")}
        leaders = build_sector_leaders(_stock_frame(), pool, top_n=5)
        assert "OTHER" not in [leader.symbol for leader in leaders["SECT"]]

    def test_one_entry_per_pool_sector(self):
        pool = {"A": ("HOT",), "B": ("COLD",)}
        leaders = build_sector_leaders(_stock_frame(), pool)
        assert set(leaders) == {"A", "B"}

    def test_performance_fields_populated(self):
        pool = {"SECT": ("HOT",)}
        leader = build_sector_leaders(_stock_frame(), pool)["SECT"][0]
        assert leader.perf_1m > 0
        assert leader.perf_3m > 0

    def test_empty_pool_yields_empty_dict(self):
        assert build_sector_leaders(_stock_frame(), {}) == {}
