import numpy as np
import pandas as pd

from portfoy import config, trend_scan
from portfoy.trend_scan import TrendCandidate, build_trend_scan, scan_symbol

N = 260  # > TREND_MA_SLOW + swing window padding, with room for several swings


def _trending_df(direction: str = "up", n: int = N) -> pd.DataFrame:
    """n-bar fixture with an unmistakable zigzag: a HH+HL sequence
    (direction="up") or LH+LL sequence (direction="down"), riding a linear
    drift + sine wave so swing_highs/swing_lows confirm several pivots."""
    drift = np.linspace(0.0, 60.0, n) if direction == "up" else np.linspace(60.0, 0.0, n)
    wave = 4.0 * np.sin(np.linspace(0, 20, n))
    close = 100.0 + drift + wave
    return pd.DataFrame(
        {"Close": close, "High": close + 1.0, "Low": close - 1.0, "Volume": 1_000_000.0}
    )


def _sideways_df(n: int = N) -> pd.DataFrame:
    """A flat oscillation -- no linear drift, so no confirmed HH+HL or
    LH+LL sequence. Represents the video's "consolidation" market state."""
    wave = 5.0 * np.sin(np.linspace(0, 24, n))
    close = 100.0 + wave
    return pd.DataFrame(
        {"Close": close, "High": close + 1.0, "Low": close - 1.0, "Volume": 1_000_000.0}
    )


class TestScanSymbol:
    def test_detects_strong_uptrend(self):
        candidate = scan_symbol("AAA", "Teknoloji", _trending_df("up"))
        assert isinstance(candidate, TrendCandidate)
        assert candidate.symbol == "AAA"
        assert candidate.sector == "Teknoloji"
        assert candidate.direction == "boga"
        assert candidate.score == 3
        assert candidate.strength == "guclu"
        assert candidate.ma_trend_confirmed is True
        assert candidate.trendline_confirmed is True
        assert candidate.structural_stop is not None
        assert candidate.structural_stop < candidate.price

    def test_detects_downtrend(self):
        candidate = scan_symbol("AAA", "Teknoloji", _trending_df("down"))
        assert candidate is not None
        assert candidate.direction == "ayi"
        assert candidate.structural_stop is not None
        assert candidate.structural_stop > candidate.price

    def test_none_on_empty_history(self):
        assert scan_symbol("AAA", "Teknoloji", pd.DataFrame()) is None

    def test_none_on_insufficient_history(self):
        short = _trending_df("up").iloc[-40:].reset_index(drop=True)
        assert scan_symbol("AAA", "Teknoloji", short) is None

    def test_none_on_sideways_consolidation(self):
        # The video's core distinction: a market is either trending or
        # consolidating. A flat oscillation has no HH+HL/LH+LL sequence, so
        # it must not surface as a trend candidate -- this is the Layer-1
        # hard gate, not a scoring nuance.
        assert scan_symbol("AAA", "Teknoloji", _sideways_df()) is None

    def test_score_matches_confirmed_layers(self):
        for direction in ("up", "down"):
            candidate = scan_symbol("AAA", "Teknoloji", _trending_df(direction))
            assert candidate is not None
            expected = (
                1 + int(candidate.ma_trend_confirmed) + int(bool(candidate.trendline_confirmed))
            )
            assert candidate.score == expected
            assert candidate.strength == {1: "erken", 2: "olusuyor", 3: "guclu"}[candidate.score]

    def test_volume_confirmed_false_on_flat_volume(self):
        # _trending_df's volume is a flat constant -- the recent-vs-20d
        # average comparison is never strictly greater, so this must be False,
        # not a fluke True from a >= boundary.
        candidate = scan_symbol("AAA", "Teknoloji", _trending_df("up"))
        assert candidate is not None
        assert candidate.volume_confirmed is False

    def test_volume_confirmed_true_when_recent_volume_spikes(self):
        df = _trending_df("up")
        volume = df["Volume"].to_numpy().copy()
        volume[-config.TREND_VOLUME_RECENT_DAYS :] *= 3.0
        df["Volume"] = volume
        candidate = scan_symbol("AAA", "Teknoloji", df)
        assert candidate is not None
        assert candidate.volume_confirmed is True

    def test_money_flow_and_adx_fields_are_well_formed(self):
        candidate = scan_symbol("AAA", "Teknoloji", _trending_df("up"))
        assert candidate is not None
        assert candidate.money_flow_signal in {"accumulation", "distribution", "notr"}
        assert isinstance(candidate.money_flow_aligned, bool)
        assert candidate.adx is not None and candidate.adx > 0
        assert candidate.adx_rising in (True, False)
        assert candidate.trend_maturity in {"zayif", "saglikli", "tukenebilir", "belirsiz"}

    def test_trend_age_and_freshness_are_consistent(self):
        candidate = scan_symbol("AAA", "Teknoloji", _trending_df("up"))
        assert candidate is not None
        assert candidate.trend_age_days >= 0
        assert candidate.newly_triggered == (
            candidate.trend_age_days <= config.TREND_FRESH_MAX_AGE_DAYS
        )


class TestRsiDivergenceHelper:
    def test_bearish_divergence_flagged_when_rsi_fails_to_confirm_new_high(self):
        # Price makes a higher high (105 -> 110) but RSI makes a lower high
        # at that same pivot (65 -> 60) -- classic exhaustion warning.
        rsi_series = pd.Series([50.0, 55.0, 65.0, 45.0, 60.0])
        swing_high_pos = np.array([1, 2, 4])
        swing_high_px = np.array([100.0, 105.0, 110.0])
        swing_low_pos = np.array([0, 3])
        swing_low_px = np.array([95.0, 99.0])
        warning = trend_scan._rsi_divergence(
            "boga", rsi_series, swing_high_pos, swing_high_px, swing_low_pos, swing_low_px
        )
        assert warning is True

    def test_no_divergence_when_rsi_confirms_the_new_high(self):
        rsi_series = pd.Series([50.0, 55.0, 60.0, 65.0, 70.0])
        swing_high_pos = np.array([1, 2, 4])
        swing_high_px = np.array([100.0, 105.0, 110.0])
        swing_low_pos = np.array([0, 3])
        swing_low_px = np.array([95.0, 99.0])
        warning = trend_scan._rsi_divergence(
            "boga", rsi_series, swing_high_pos, swing_high_px, swing_low_pos, swing_low_px
        )
        assert warning is False

    def test_bullish_divergence_flagged_for_downtrend(self):
        # Price makes a lower low (95 -> 90) but RSI makes a higher low at
        # that pivot (30 -> 35) -- downtrend exhaustion warning.
        rsi_series = pd.Series([50.0, 45.0, 30.0, 55.0, 35.0])
        swing_high_pos = np.array([0, 3])
        swing_high_px = np.array([105.0, 101.0])
        swing_low_pos = np.array([1, 2, 4])
        swing_low_px = np.array([98.0, 95.0, 90.0])
        warning = trend_scan._rsi_divergence(
            "ayi", rsi_series, swing_high_pos, swing_high_px, swing_low_pos, swing_low_px
        )
        assert warning is True


class TestBuildTrendScan:
    def test_skips_symbols_with_insufficient_history(self, monkeypatch):
        monkeypatch.setattr(trend_scan.data, "get_histories", lambda symbols, period=None: {})
        assert build_trend_scan({"AAA": "Test"}) == []

    def test_includes_and_labels_matching_symbols(self, monkeypatch):
        histories = {"AAA": _trending_df("up"), "BBB": _sideways_df()}
        monkeypatch.setattr(
            trend_scan.data, "get_histories", lambda symbols, period=None: histories
        )
        out = build_trend_scan({"AAA": "Enerji", "BBB": "Finans"})
        assert [c.symbol for c in out] == ["AAA"]
        assert out[0].sector == "Enerji"

    def test_empty_universe_produces_empty_scan(self, monkeypatch):
        monkeypatch.setattr(trend_scan.data, "get_histories", lambda symbols, period=None: {})
        assert build_trend_scan({}) == []

    def test_results_are_sorted_strongest_first(self, monkeypatch):
        histories = {"AAA": _trending_df("up"), "BBB": _trending_df("down")}
        monkeypatch.setattr(
            trend_scan.data, "get_histories", lambda symbols, period=None: histories
        )
        out = build_trend_scan({"AAA": "Teknoloji", "BBB": "Enerji"})
        assert len(out) == 2
        assert out[0].score >= out[1].score
