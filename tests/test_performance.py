import numpy as np
import pandas as pd
import pytest

from portfoy.performance import (
    compare,
    convert,
    portfolio_series,
    rebase,
    to_daily,
    total_return,
    window_start,
)

DAYS = 300


def _series(values) -> pd.Series:
    index = pd.date_range("2025-09-01", periods=len(values), freq="B")
    return pd.Series(values, index=index)


@pytest.fixture
def flat_fx():
    """A steady 40.00 USD/TRY series."""
    return _series(np.full(DAYS, 40.0))


def _tz_series(values, tz: str, hour: int) -> pd.Series:
    """Exchange-style series: tz-aware, stamped at that market's closing hour."""
    index = pd.date_range(f"2025-09-01 {hour:02d}:00", periods=len(values), freq="B", tz=tz)
    return pd.Series(values, index=index)


class TestToDaily:
    def test_strips_timezone(self):
        result = to_daily(_tz_series(np.full(10, 100.0), "America/New_York", 16))
        assert result.index.tz is None

    def test_normalises_to_midnight(self):
        result = to_daily(_tz_series(np.full(10, 100.0), "America/New_York", 16))
        assert (result.index == result.index.normalize()).all()

    def test_preserves_values(self):
        values = np.linspace(100.0, 110.0, 10)
        assert to_daily(_tz_series(values, "Europe/Istanbul", 18)).iloc[-1] == pytest.approx(110.0)

    def test_deduplicates_keeping_last(self):
        index = pd.DatetimeIndex(["2026-01-05 09:00", "2026-01-05 17:00"])
        result = to_daily(pd.Series([1.0, 2.0], index=index))
        assert len(result) == 1 and result.iloc[0] == 2.0

    def test_empty_series(self):
        assert to_daily(pd.Series(dtype=float)).empty


class TestCrossTimezoneAlignment:
    """Regression: exchanges stamp bars in their own timezone and must still align."""

    def test_ny_asset_converts_against_utc_fx(self):
        prices = _tz_series(np.full(60, 100.0), "America/New_York", 16)
        fx = _tz_series(np.full(60, 40.0), "UTC", 0)
        converted = convert(prices, "USD", "TRY", fx)
        assert not converted.empty
        assert converted.iloc[-1] == pytest.approx(4000.0)

    def test_istanbul_asset_converts_against_utc_fx(self):
        prices = _tz_series(np.full(60, 4000.0), "Europe/Istanbul", 18)
        fx = _tz_series(np.full(60, 40.0), "UTC", 0)
        converted = convert(prices, "TRY", "USD", fx)
        assert not converted.empty
        assert converted.iloc[-1] == pytest.approx(100.0)

    def test_benchmarks_across_timezones_all_survive(self):
        fx = _tz_series(np.full(60, 40.0), "UTC", 0)
        benchmarks = {
            "^GSPC": _tz_series(np.linspace(100.0, 110.0, 60), "America/New_York", 16),
            "XU100.IS": _tz_series(np.linspace(100.0, 120.0, 60), "Europe/Istanbul", 18),
            "BTC-USD": _tz_series(np.linspace(100.0, 90.0, 60), "UTC", 0),
        }
        labels = {
            "^GSPC": ("S&P 500", "S&P 500", "USD"),
            "XU100.IS": ("BIST 100", "BIST 100", "TRY"),
            "BTC-USD": ("Bitcoin", "Bitcoin", "USD"),
        }
        results = compare(pd.Series(dtype=float), benchmarks, "TRY", fx, "per_1y", labels)
        assert {r.key for r in results} == set(benchmarks)

    def test_portfolio_of_mixed_market_holdings(self):
        fx = _tz_series(np.full(60, 40.0), "UTC", 0)
        prices = {
            "AAPL": _tz_series(np.linspace(100.0, 200.0, 60), "America/New_York", 16),
            "THYAO.IS": _tz_series(np.linspace(100.0, 200.0, 60), "Europe/Istanbul", 18),
        }
        index = portfolio_series(
            {"AAPL": 0.5, "THYAO.IS": 0.5}, prices,
            {"AAPL": "USD", "THYAO.IS": "TRY"}, "TRY", fx, None,
        )
        assert not index.empty
        assert total_return(index) == pytest.approx(100.0)


class TestConvert:
    def test_same_currency_passthrough(self, flat_fx):
        prices = _series(np.full(DAYS, 100.0))
        assert convert(prices, "USD", "USD", flat_fx).equals(prices)

    def test_usd_asset_into_try(self, flat_fx):
        prices = _series(np.full(DAYS, 100.0))
        assert convert(prices, "USD", "TRY", flat_fx).iloc[-1] == pytest.approx(4000.0)

    def test_try_asset_into_usd(self, flat_fx):
        prices = _series(np.full(DAYS, 4000.0))
        assert convert(prices, "TRY", "USD", flat_fx).iloc[-1] == pytest.approx(100.0)

    def test_rising_fx_boosts_usd_asset_in_try(self):
        prices = _series(np.full(DAYS, 100.0))
        fx = _series(np.linspace(30.0, 60.0, DAYS))
        converted = convert(prices, "USD", "TRY", fx)
        assert converted.iloc[-1] == pytest.approx(2.0 * converted.iloc[0])


class TestRebaseAndReturn:
    def test_rebase_starts_at_100(self):
        rebased = rebase(_series(np.linspace(50.0, 75.0, DAYS)), None)
        assert rebased.iloc[0] == pytest.approx(100.0)

    def test_rebase_reflects_growth(self):
        rebased = rebase(_series(np.linspace(50.0, 75.0, DAYS)), None)
        assert rebased.iloc[-1] == pytest.approx(150.0)

    def test_rebase_honours_start(self):
        prices = _series(np.linspace(100.0, 200.0, DAYS))
        start = prices.index[-11]
        rebased = rebase(prices, start)
        assert len(rebased) == 11
        assert rebased.iloc[0] == pytest.approx(100.0)

    def test_total_return(self):
        assert total_return(_series([100.0, 120.0])) == pytest.approx(20.0)

    def test_total_return_short_series(self):
        assert total_return(_series([100.0])) == 0.0
        assert total_return(pd.Series(dtype=float)) == 0.0

    def test_zero_first_value_is_safe(self):
        assert total_return(_series([0.0, 50.0])) == 0.0


class TestWindowStart:
    def test_picks_n_bars_back(self):
        index = _series(np.zeros(DAYS)).index
        assert window_start(index, "per_1m") == index[-22]

    def test_short_history_falls_back_to_first_bar(self):
        index = _series(np.zeros(5)).index
        assert window_start(index, "per_1y") == index[0]

    def test_empty_index(self):
        assert window_start(pd.Index([]), "per_1m") is None

    def test_ytd_starts_within_current_year(self):
        index = _series(np.zeros(DAYS)).index
        start = window_start(index, "per_ytd")
        assert start.year == index[-1].year


class TestPortfolioSeries:
    def _prices(self):
        return {
            "AAA": _series(np.linspace(100.0, 200.0, DAYS)),   # +100%
            "BBB": _series(np.full(DAYS, 50.0)),               # flat
        }

    def test_single_holding_tracks_that_asset(self, flat_fx):
        index = portfolio_series(
            {"AAA": 1.0}, self._prices(), {"AAA": "USD"}, "USD", flat_fx, None
        )
        assert total_return(index) == pytest.approx(100.0)

    def test_equal_weights_average_the_returns(self, flat_fx):
        index = portfolio_series(
            {"AAA": 0.5, "BBB": 0.5}, self._prices(),
            {"AAA": "USD", "BBB": "USD"}, "USD", flat_fx, None,
        )
        assert total_return(index) == pytest.approx(50.0)

    def test_cash_drags_the_return_down(self, flat_fx):
        index = portfolio_series(
            {"AAA": 0.5}, self._prices(), {"AAA": "USD"}, "USD", flat_fx, None,
            cash_weight=0.5,
        )
        assert total_return(index) == pytest.approx(50.0)

    def test_all_cash_returns_zero(self, flat_fx):
        index = portfolio_series(
            {"AAA": 0.0}, self._prices(), {"AAA": "USD"}, "USD", flat_fx, None,
            cash_weight=1.0,
        )
        assert index.empty or total_return(index) == pytest.approx(0.0)

    def test_starts_at_100(self, flat_fx):
        index = portfolio_series(
            {"AAA": 0.5, "BBB": 0.5}, self._prices(),
            {"AAA": "USD", "BBB": "USD"}, "USD", flat_fx, None,
        )
        assert index.iloc[0] == pytest.approx(100.0)

    def test_missing_price_series_skipped(self, flat_fx):
        index = portfolio_series(
            {"AAA": 0.5, "GONE": 0.5}, self._prices(),
            {"AAA": "USD"}, "USD", flat_fx, None,
        )
        assert total_return(index) == pytest.approx(100.0)

    def test_no_usable_holdings_returns_empty(self, flat_fx):
        assert portfolio_series({}, {}, {}, "USD", flat_fx, None).empty

    def test_try_holding_compared_in_usd(self, flat_fx):
        prices = {"TRY_STOCK": _series(np.linspace(4000.0, 8000.0, DAYS))}
        index = portfolio_series(
            {"TRY_STOCK": 1.0}, prices, {"TRY_STOCK": "TRY"}, "USD", flat_fx, None
        )
        assert total_return(index) == pytest.approx(100.0)


class TestCompare:
    def _benchmarks(self):
        return {
            "^GSPC": _series(np.linspace(100.0, 110.0, DAYS)),   # +10%
            "XU100.IS": _series(np.linspace(100.0, 130.0, DAYS)),  # +30%
        }

    def _labels(self):
        return {
            "^GSPC": ("S&P 500", "S&P 500", "USD"),
            "XU100.IS": ("BIST 100", "BIST 100", "TRY"),
        }

    def test_sorted_best_first(self, flat_fx):
        results = compare(pd.Series(dtype=float), self._benchmarks(), "TRY",
                          flat_fx, "per_1y", self._labels())
        returns = [r.return_pct for r in results]
        assert returns == sorted(returns, reverse=True)

    def test_portfolio_included_when_present(self, flat_fx):
        portfolio = rebase(_series(np.linspace(100.0, 150.0, DAYS)), None)
        results = compare(portfolio, self._benchmarks(), "TRY",
                          flat_fx, "per_1y", self._labels())
        mine = next(r for r in results if r.key == "portfolio")
        assert mine.return_pct == pytest.approx(50.0)
        assert results[0].key == "portfolio"

    def test_empty_portfolio_omitted(self, flat_fx):
        results = compare(pd.Series(dtype=float), self._benchmarks(), "TRY",
                          flat_fx, "per_1y", self._labels())
        assert all(r.key != "portfolio" for r in results)

    def test_labels_localised(self, flat_fx):
        results = compare(pd.Series(dtype=float), self._benchmarks(), "TRY",
                          flat_fx, "per_1y", self._labels())
        assert {r.label("tr") for r in results} == {"S&P 500", "BIST 100"}

    def test_usd_asset_gains_in_try_when_dollar_rises(self):
        # Shorter than one year, so the window covers the whole series and the
        # expected return is exactly the FX move.
        short = 100
        fx = _series(np.linspace(30.0, 60.0, short))
        benchmarks = {"^GSPC": _series(np.full(short, 100.0))}
        labels = {"^GSPC": ("S&P 500", "S&P 500", "USD")}
        in_try = compare(pd.Series(dtype=float), benchmarks, "TRY", fx, "per_1y", labels)
        in_usd = compare(pd.Series(dtype=float), benchmarks, "USD", fx, "per_1y", labels)
        assert in_try[0].return_pct == pytest.approx(100.0)
        assert in_usd[0].return_pct == pytest.approx(0.0)

    def test_period_window_limits_the_measured_return(self, flat_fx):
        rising = {"^GSPC": _series(np.linspace(100.0, 200.0, DAYS))}
        labels = {"^GSPC": ("S&P 500", "S&P 500", "USD")}
        one_month = compare(pd.Series(dtype=float), rising, "USD",
                            flat_fx, "per_1m", labels)[0]
        one_year = compare(pd.Series(dtype=float), rising, "USD",
                           flat_fx, "per_1y", labels)[0]
        assert one_month.return_pct < one_year.return_pct

    def test_no_benchmarks_returns_only_portfolio(self, flat_fx):
        portfolio = rebase(_series(np.linspace(100.0, 120.0, DAYS)), None)
        results = compare(portfolio, {}, "USD", flat_fx, "per_1y", {})
        assert len(results) == 1 and results[0].key == "portfolio"
