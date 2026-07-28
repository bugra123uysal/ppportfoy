import pytest

from portfoy.sentiment import (
    breadth_score,
    build_score,
    momentum_score,
    put_call_score,
    vix_score,
)


class TestComponentScores:
    def test_vix_calm_is_greedy(self):
        assert vix_score(10.0) == pytest.approx(100.0)

    def test_vix_panic_is_fearful(self):
        assert vix_score(40.0) == pytest.approx(0.0)

    def test_vix_mid(self):
        assert vix_score(25.0) == pytest.approx(50.0)

    def test_vix_clipped(self):
        assert vix_score(80.0) == 0.0
        assert vix_score(5.0) == 100.0

    def test_momentum_at_average_is_neutral(self):
        assert momentum_score(100.0, 100.0) == pytest.approx(50.0)

    def test_momentum_10pct_above_is_max(self):
        assert momentum_score(110.0, 100.0) == pytest.approx(100.0)

    def test_momentum_10pct_below_is_min(self):
        assert momentum_score(90.0, 100.0) == pytest.approx(0.0)

    def test_momentum_bad_sma_is_neutral(self):
        assert momentum_score(100.0, 0.0) == 50.0

    def test_breadth_passthrough_clipped(self):
        assert breadth_score(65.0) == 65.0
        assert breadth_score(140.0) == 100.0

    def test_put_call_extremes(self):
        assert put_call_score(1.5) == pytest.approx(0.0)
        assert put_call_score(0.5) == pytest.approx(100.0)
        assert put_call_score(1.0) == pytest.approx(50.0)


class TestBuildScore:
    def test_composite_is_mean_of_components(self):
        score = build_score(vix=25.0, pct_above_200=70.0)   # 50 and 70
        assert score.composite == pytest.approx(60.0)
        assert set(score.components) == {"vix", "breadth"}

    def test_missing_inputs_are_skipped(self):
        score = build_score(vix=25.0, price=100.0, sma=None)
        assert set(score.components) == {"vix"}

    def test_no_inputs_returns_none(self):
        assert build_score() is None

    @pytest.mark.parametrize(
        ("composite_inputs", "label"),
        [
            ({"vix": 40.0}, "extreme_fear"),          # score 0
            ({"vix": 30.0}, "fear"),                  # ~33
            ({"vix": 25.0}, "neutral"),               # 50
            ({"vix": 20.0}, "greed"),                 # ~67
            ({"vix": 12.0}, "extreme_greed"),         # ~93
        ],
    )
    def test_labels(self, composite_inputs, label):
        assert build_score(**composite_inputs).label == label
