import numpy as np
import pandas as pd
import pytest

from portfoy import trade_scan
from portfoy.indicators import atr
from portfoy.trade_scan import (
    TradeSignal,
    _crossed_down,
    _crossed_up,
    _group1_buy_momentum_volume_bands,
    _group1_sell_momentum_volume_bands,
    _group2_buy_trend_deviation_stochrsi,
    _group2_sell_trend_deviation_stochrsi,
    _group3_buy_flip_and_trend,
    _group3_sell_flip_and_trend,
    _group4_buy_stochrsi_ema_median,
    _group4_sell_stochrsi_ema,
    _median_trend_up,
    _weekly_trend_up,
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

# A 35-bar uptrend feeding Stochastic RSI's warmup, then a 25-bar dip/rally
# tail -- calibrated (via randomized search, not hand-derived like the
# fixtures above) so that on the final bar: the 3-period Median indicator
# reads bullish (median of hl2 above its own EMA) *and* %K of the 14d
# Stochastic RSI crosses up through its own 14d EMA. Group 4's confirming
# indicators only become valid a handful of bars before the end (Stoch
# RSI -> its EMA needs ~14+14+14 bars of warmup), so unlike Groups 1-3 this
# fixture can't be described as a simple trend shape -- it's the shortest
# series found where both conditions land on the same final bar.
_GROUP4_BUY_CLOSE = [
    100.0, 100.8824, 101.7647, 102.6471, 103.5294, 104.4118, 105.2941, 106.1765, 107.0588,
    107.9412, 108.8235, 109.7059, 110.5882, 111.4706, 112.3529, 113.2353, 114.1176, 115.0,
    115.8824, 116.7647, 117.6471, 118.5294, 119.4118, 120.2941, 121.1765, 122.0588, 122.9412,
    123.8235, 124.7059, 125.5882, 126.4706, 127.3529, 128.2353, 129.1176, 130.0, 128.5158,
    130.7082, 134.1262, 137.519, 143.2725, 142.417, 144.3495, 143.5508, 139.5763, 137.7647,
    138.4732, 136.0277, 135.7533, 139.414, 141.4254, 143.4424, 144.7778, 144.5519, 139.2487,
    142.5231, 138.3031, 139.2514, 139.2262, 139.938, 140.995,
]


def _mirror(prices: list[float]) -> list[float]:
    """Reflect a price series about 150 -- turns every bullish fixture above
    into its bearish mirror image (uptrend <-> downtrend, dip <-> rally,
    green <-> red final candle), since every indicator used by Groups 1-4
    (SMI, Bollinger, EMA, StochRSI, CCI, the ATR trailing stop, the Median
    indicator) is a function of price differences/ratios and so behaves
    symmetrically under this reflection.
    """
    return [300.0 - p for p in prices]


# Bearish mirror of _GROUP1_CLOSE/_OPEN/_VOLUME: an uptrend, then a sharp
# last-bar drop on a red candle + volume spike -- SMI turns down from
# above zero, closing below its signal line, with a Bollinger break below
# the mid band.
_GROUP1_SELL_CLOSE = _mirror(_GROUP1_CLOSE)
_GROUP1_SELL_OPEN = [*_GROUP1_SELL_CLOSE[:-1], 200.0]
_GROUP1_SELL_VOLUME = _GROUP1_VOLUME

# Bearish mirror of _GROUP2_CLOSE: a downtrend (21d EMA falling) with an
# 8-bar relief-rally tail ending >5% above that EMA, and Stochastic RSI
# %K crossing back below %D on the final bar.
_GROUP2_SELL_CLOSE = _mirror(_GROUP2_CLOSE)

# Bearish mirror of _GROUP3_CLOSE: a steady uptrend, then a sharp last-bar
# drop -- an ATR trailing-stop (UT Bot) flip to sell, with CCI negative.
_GROUP3_SELL_CLOSE = _mirror(_GROUP3_CLOSE)

# Bearish mirror of _GROUP4_BUY_CLOSE: %K crosses down through its own EMA
# on the final bar (Group 4's sell side needs no Median confirmation, per
# the module docstring, but the mirror still reads Median-bearish too).
_GROUP4_SELL_CLOSE = _mirror(_GROUP4_BUY_CLOSE)


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


class TestCrossedDown:
    def test_true_on_fresh_cross(self):
        assert _crossed_down(pd.Series([5.0, 1.0]), pd.Series([2.0, 3.0])) is True

    def test_false_when_already_below(self):
        assert _crossed_down(pd.Series([1.0, 0.5]), pd.Series([2.0, 3.0])) is False

    def test_false_when_still_above(self):
        assert _crossed_down(pd.Series([5.0, 4.0]), pd.Series([2.0, 3.0])) is False

    def test_false_on_short_series(self):
        assert _crossed_down(pd.Series([2.0]), pd.Series([1.0])) is False

    def test_false_on_nan(self):
        assert _crossed_down(pd.Series([np.nan, 1.0]), pd.Series([2.0, 3.0])) is False


class TestGroup1BuyMomentumVolumeBands:
    def test_fires_on_engineered_reversal(self):
        df = _frame(_GROUP1_CLOSE, _GROUP1_OPEN, _GROUP1_VOLUME)
        assert _group1_buy_momentum_volume_bands(df) is True

    def test_false_on_flat_series(self):
        df = _frame(np.full(N, 100.0).tolist())
        assert _group1_buy_momentum_volume_bands(df) is False

    def test_false_without_volume_confirmation(self):
        # Same reversal, but volume never exceeds its 20d average.
        df = _frame(_GROUP1_CLOSE, _GROUP1_OPEN, [1000.0] * N)
        assert _group1_buy_momentum_volume_bands(df) is False


class TestGroup1SellMomentumVolumeBands:
    def test_fires_on_engineered_reversal(self):
        df = _frame(_GROUP1_SELL_CLOSE, _GROUP1_SELL_OPEN, _GROUP1_SELL_VOLUME)
        assert _group1_sell_momentum_volume_bands(df) is True

    def test_false_on_flat_series(self):
        df = _frame(np.full(N, 100.0).tolist())
        assert _group1_sell_momentum_volume_bands(df) is False

    def test_false_without_volume_confirmation(self):
        # Same reversal, but volume never exceeds its 20d average.
        df = _frame(_GROUP1_SELL_CLOSE, _GROUP1_SELL_OPEN, [1000.0] * N)
        assert _group1_sell_momentum_volume_bands(df) is False


class TestGroup2BuyTrendDeviationStochRsi:
    def test_fires_on_engineered_pullback(self):
        df = _frame(_GROUP2_CLOSE)
        assert _group2_buy_trend_deviation_stochrsi(df) is True

    def test_false_on_clean_uptrend_no_dip(self):
        close = np.linspace(100, 150, N).tolist()
        df = _frame(close)
        assert _group2_buy_trend_deviation_stochrsi(df) is False

    def test_false_on_downtrend(self):
        close = np.linspace(150, 100, N).tolist()
        df = _frame(close)
        assert _group2_buy_trend_deviation_stochrsi(df) is False


class TestGroup2SellTrendDeviationStochRsi:
    def test_fires_on_engineered_rally(self):
        df = _frame(_GROUP2_SELL_CLOSE)
        assert _group2_sell_trend_deviation_stochrsi(df) is True

    def test_false_on_clean_downtrend_no_rally(self):
        close = np.linspace(150, 100, N).tolist()
        df = _frame(close)
        assert _group2_sell_trend_deviation_stochrsi(df) is False

    def test_false_on_uptrend(self):
        close = np.linspace(100, 150, N).tolist()
        df = _frame(close)
        assert _group2_sell_trend_deviation_stochrsi(df) is False


class TestGroup3BuyFlipAndTrend:
    def test_fires_on_engineered_flip(self):
        df = _frame(_GROUP3_CLOSE)
        assert _group3_buy_flip_and_trend(df) is True

    def test_false_on_pure_downtrend(self):
        close = np.linspace(150, 100, N).tolist()
        df = _frame(close)
        assert _group3_buy_flip_and_trend(df) is False


class TestGroup3SellFlipAndTrend:
    def test_fires_on_engineered_flip(self):
        df = _frame(_GROUP3_SELL_CLOSE)
        assert _group3_sell_flip_and_trend(df) is True

    def test_false_on_pure_uptrend(self):
        close = np.linspace(100, 150, N).tolist()
        df = _frame(close)
        assert _group3_sell_flip_and_trend(df) is False


class TestMedianTrendUp:
    def test_true_on_uptrend(self):
        df = _frame(np.linspace(100, 150, N).tolist())
        assert _median_trend_up(df) is True

    def test_false_on_downtrend(self):
        df = _frame(np.linspace(150, 100, N).tolist())
        assert _median_trend_up(df) is False

    def test_none_on_insufficient_history(self):
        df = _frame([100.0, 101.0])
        assert _median_trend_up(df) is None


class TestGroup4BuyStochRsiEmaMedian:
    def test_fires_on_engineered_reversal(self):
        df = _frame(_GROUP4_BUY_CLOSE)
        assert _group4_buy_stochrsi_ema_median(df) is True

    def test_false_on_flat_series(self):
        df = _frame(np.full(N, 100.0).tolist())
        assert _group4_buy_stochrsi_ema_median(df) is False

    def test_false_without_median_confirmation(self):
        # Same Close series as the fixture above (so %K still crosses up
        # through its own EMA), but High/Low decoupled from Close into a
        # plain downtrend -- Median (which reads hl2, not Close) is
        # bearish, so the buy side must not fire even though the
        # Stochastic RSI leg alone would qualify.
        close = np.array(_GROUP4_BUY_CLOSE)
        decoupled = np.linspace(150, 100, N)
        df = pd.DataFrame(
            {
                "Open": close,
                "High": decoupled + 1.0,
                "Low": decoupled - 1.0,
                "Close": close,
                "Volume": np.full(N, 1000.0),
            }
        )
        assert _median_trend_up(df) is False
        assert _group4_buy_stochrsi_ema_median(df) is False


class TestGroup4SellStochRsiEma:
    def test_fires_on_engineered_reversal(self):
        df = _frame(_GROUP4_SELL_CLOSE)
        assert _group4_sell_stochrsi_ema(df) is True

    def test_false_on_flat_series(self):
        df = _frame(np.full(N, 100.0).tolist())
        assert _group4_sell_stochrsi_ema(df) is False


class TestWeeklyTrendUp:
    def _dated_frame(self, close: np.ndarray) -> pd.DataFrame:
        index = pd.date_range("2024-01-01", periods=len(close), freq="B")
        return pd.DataFrame(
            {
                "Open": close, "High": close + 1.0, "Low": close - 1.0, "Close": close,
                "Volume": np.full(len(close), 1000.0),
            },
            index=index,
        )

    def test_none_without_datetime_index(self):
        df = _frame(np.linspace(100, 200, N).tolist())
        assert _weekly_trend_up(df) is None

    def test_true_on_weekly_uptrend(self):
        df = self._dated_frame(np.linspace(100.0, 300.0, 400))
        assert _weekly_trend_up(df) is True

    def test_false_on_weekly_downtrend(self):
        df = self._dated_frame(np.linspace(300.0, 100.0, 400))
        assert _weekly_trend_up(df) is False

    def test_none_on_short_history(self):
        df = self._dated_frame(np.linspace(100.0, 110.0, 30))
        assert _weekly_trend_up(df) is None


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
        assert signal.direction == "long"
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
        assert signal.pct_from_52w_high is not None and signal.pct_from_52w_high <= 0
        assert signal.pct_from_52w_low is not None and signal.pct_from_52w_low >= 0
        # _frame() fixtures use a plain integer index, not a DatetimeIndex,
        # so weekly resampling can't run -- None, not True/False.
        assert signal.weekly_trend_aligned is None

    def test_includes_and_labels_short_signals(self, monkeypatch):
        histories = {
            "AAA": _frame(_GROUP1_SELL_CLOSE, _GROUP1_SELL_OPEN, _GROUP1_SELL_VOLUME),
        }
        monkeypatch.setattr(
            trade_scan.data, "get_history", lambda sym, period=None: histories[sym]
        )
        out = build_trade_scan({"AAA": "Enerji"})
        assert [s.symbol for s in out] == ["AAA"]

        signal = out[0]
        assert signal.direction == "short"
        # Mirror of the long fixture above: also satisfies Group 3's
        # bearish ATR-flip condition.
        assert signal.groups == [1, 3]
        assert signal.price == pytest.approx(175.0)

        expected_atr = atr(
            histories["AAA"]["High"], histories["AAA"]["Low"], histories["AAA"]["Close"], 14
        ).iloc[-1]
        assert signal.suggested_stop == pytest.approx(round(175.0 + expected_atr * 1.5, 2))

    def test_symbol_can_produce_both_a_long_and_a_short_signal(self, monkeypatch):
        # Group 1 buy (SMI-driven) and Group 2 sell (EMA-trend-driven)
        # check unrelated indicators, so nothing stops a symbol from
        # qualifying on both sides on the same day -- each direction must
        # still surface as its own independent TradeSignal.
        df = _frame(_GROUP1_CLOSE, _GROUP1_OPEN, _GROUP1_VOLUME)
        monkeypatch.setattr(trade_scan, "_group2_sell_trend_deviation_stochrsi", lambda _df: True)
        monkeypatch.setattr(trade_scan.data, "get_history", lambda sym, period=None: df)

        out = build_trade_scan({"AAA": "Enerji"})
        assert {s.direction for s in out} == {"long", "short"}
        assert len(out) == 2
