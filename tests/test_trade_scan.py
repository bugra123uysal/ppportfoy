import numpy as np
import pandas as pd
import pytest

from portfoy import trade_scan
from portfoy.indicators import atr
from portfoy.trade_scan import (
    TradeSignal,
    _crossed_up,
    _group1_momentum_volume_bands,
    _group2_trend_deviation_stochrsi,
    _group3_flip_and_trend,
    build_trade_scan,
)

N = 60


def _frame(
    close: list[float],
    open_: list[float] | None = None,
    volume: list[float] | None = None,
) -> pd.DataFrame:
    close = np.array(close, dtype=float)
    default_volume = np.full(len(close), 1000.0)
    return pd.DataFrame(
        {
            "Open": np.array(open_, dtype=float) if open_ is not None else close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.array(volume, dtype=float) if volume is not None else default_volume,
        }
    )


# A steady downtrend with light noise, then a sharp last-bar bounce back up to
# 125 on a volume spike -- engineered (see plan) so SMI turns up from below
# zero, the last candle is green on above-average volume, and the close
# crosses back above the Bollinger mid band, all on the final bar.
_GROUP1_CLOSE = [
    200.6123, 197.5092, 196.6772, 194.6573, 192.9677, 191.3146, 189.0492, 187.8615, 185.9473,
    185.4797, 182.8264, 180.9287, 179.226, 177.3858, 175.5455, 174.0207, 172.5584, 170.6181,
    169.2528, 167.1814, 165.5245, 164.2568, 162.2325, 160.1933, 158.5658, 157.0587, 155.7529,
    153.3674, 151.6511, 150.3007, 148.0099, 146.4642, 145.0923, 143.2776, 141.4068, 139.8562,
    137.0826, 136.5133, 134.1949, 132.258, 131.1174, 129.5205, 127.4528, 125.5391, 124.1458,
    122.398, 121.1113, 119.1897, 117.2995, 115.8507, 113.7314, 111.7912, 110.52, 108.7955,
    106.8321, 104.9376, 103.517, 100.976, 100.207, 125.0,
]
_GROUP1_OPEN = [*_GROUP1_CLOSE[:-1], 100.0]
_GROUP1_VOLUME = [*([1000.0] * (N - 1)), 3000.0]

# Steady uptrend (noisy) for 52 bars, then an 8-bar dip-and-partial-recovery
# tail -- engineered so the 21d EMA is still rising, price sits >5% below
# that EMA (a buy-the-dip pullback), and Stochastic RSI %K crosses back
# above %D, all on the final bar.
_GROUP2_CLOSE = [
    100.3456, 101.802, 102.2912, 101.638, 104.8269, 105.3483, 105.3454, 107.4439, 108.2077,
    109.1177, 109.8323, 111.331, 111.0283, 112.5822, 113.2434, 115.3047, 115.726, 116.3742,
    116.8652, 118.3703, 119.616, 120.3126, 122.8627, 123.5557, 120.8182, 122.6208, 125.3154,
    126.0484, 127.6646, 128.6487, 131.5296, 129.2801, 130.9949, 134.3957, 133.98, 134.9768,
    134.7801, 134.6264, 137.4224, 138.3443, 137.9883, 139.5129, 141.1044, 141.2121, 143.039,
    144.2131, 145.1336, 145.5721, 147.6526, 148.9304, 149.3405, 149.1818, 153.2487, 152.1409,
    160.1487, 151.5796, 148.4677, 146.5237, 151.3139, 137.1184,
]

# Steady downtrend, then a sharp last-bar jump back up -- an ATR trailing
# stop (UT Bot) flip to buy on the final bar, with CCI positive (Trend
# Magic / KJ MAGIC "blue").
_GROUP3_CLOSE = [*np.linspace(200, 100, N - 1).tolist(), 140.0]


class TestCrossedUp:
    def test_true_on_fresh_cross(self):
        assert _crossed_up(pd.Series([1.0, 5.0]), pd.Series([2.0, 3.0])) is True

    def test_false_when_already_above(self):
        assert _crossed_up(pd.Series([5.0, 6.0]), pd.Series([2.0, 3.0])) is False

    def test_false_when_still_below(self):
        assert _crossed_up(pd.Series([1.0, 1.5]), pd.Series([2.0, 3.0])) is False

    def test_false_on_short_series(self):
        assert _crossed_up(pd.Series([1.0]), pd.Series([2.0])) is False

    def test_false_on_nan(self):
        assert _crossed_up(pd.Series([np.nan, 5.0]), pd.Series([2.0, 3.0])) is False


class TestGroup1MomentumVolumeBands:
    def test_fires_on_engineered_reversal(self):
        df = _frame(_GROUP1_CLOSE, _GROUP1_OPEN, _GROUP1_VOLUME)
        assert _group1_momentum_volume_bands(df) is True

    def test_false_on_flat_series(self):
        df = _frame(np.full(N, 100.0).tolist())
        assert _group1_momentum_volume_bands(df) is False

    def test_false_without_volume_confirmation(self):
        # Same reversal, but volume never exceeds its 20d average.
        df = _frame(_GROUP1_CLOSE, _GROUP1_OPEN, [1000.0] * N)
        assert _group1_momentum_volume_bands(df) is False


class TestGroup2TrendDeviationStochRsi:
    def test_fires_on_engineered_pullback(self):
        df = _frame(_GROUP2_CLOSE)
        assert _group2_trend_deviation_stochrsi(df) is True

    def test_false_on_clean_uptrend_no_dip(self):
        close = np.linspace(100, 150, N).tolist()
        df = _frame(close)
        assert _group2_trend_deviation_stochrsi(df) is False

    def test_false_on_downtrend(self):
        close = np.linspace(150, 100, N).tolist()
        df = _frame(close)
        assert _group2_trend_deviation_stochrsi(df) is False


class TestGroup3FlipAndTrend:
    def test_fires_on_engineered_flip(self):
        df = _frame(_GROUP3_CLOSE)
        assert _group3_flip_and_trend(df) is True

    def test_false_on_pure_downtrend(self):
        close = np.linspace(150, 100, N).tolist()
        df = _frame(close)
        assert _group3_flip_and_trend(df) is False


class TestBuildTradeScan:
    def test_skips_symbols_with_insufficient_history(self, monkeypatch):
        monkeypatch.setattr(trade_scan.data, "get_history", lambda sym, period=None: pd.DataFrame())
        assert build_trade_scan({"AAA": "Test"}) == []

    def test_skips_symbols_matching_no_group(self, monkeypatch):
        flat = _frame(np.full(N, 100.0).tolist())
        monkeypatch.setattr(trade_scan.data, "get_history", lambda sym, period=None: flat)
        assert build_trade_scan({"AAA": "Test"}) == []

    def test_includes_and_labels_matching_symbols(self, monkeypatch):
        histories = {
            "AAA": _frame(_GROUP1_CLOSE, _GROUP1_OPEN, _GROUP1_VOLUME),
            "BBB": _frame(np.full(N, 100.0).tolist()),
        }
        monkeypatch.setattr(
            trade_scan.data, "get_history", lambda sym, period=None: histories[sym]
        )
        out = build_trade_scan({"AAA": "Enerji", "BBB": "Finans"})
        assert [s.symbol for s in out] == ["AAA"]

        signal = out[0]
        assert isinstance(signal, TradeSignal)
        assert signal.sector == "Enerji"
        # This close series is a downtrend-then-jump, which happens to also
        # satisfy Group 3's ATR-flip condition -- a stock can qualify for
        # more than one group at once, which is the strongest kind of match.
        assert signal.groups == [1, 3]
        assert signal.price == pytest.approx(125.0)

        expected_atr = atr(
            histories["AAA"]["High"], histories["AAA"]["Low"], histories["AAA"]["Close"], 14
        ).iloc[-1]
        assert signal.atr_14 == pytest.approx(expected_atr)
        assert signal.suggested_stop == pytest.approx(round(125.0 - expected_atr * 1.5, 2))
