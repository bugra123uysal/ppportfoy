import json

import numpy as np
import pandas as pd
import pytest

from portfoy import config, report
from portfoy.data import OwnershipFlow
from portfoy.options import OptionActivity
from portfoy.report import (
    SymbolContext,
    SymbolReport,
    build_report,
    build_symbol_context,
    score_symbol,
)
from portfoy.serialize import dumps

N = 300  # ~14 months of business days -- enough for SMA200 and the weekly-trend check


def _uptrend_df(
    n: int = N, start: float = 100.0, end: float = 220.0, seed: int = 7
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    trend = np.linspace(start, end, n)
    noise = rng.normal(0.0, 0.6, n)
    close = trend + noise
    high = close + np.abs(rng.normal(0.5, 0.3, n))
    low = close - np.abs(rng.normal(0.5, 0.3, n))
    volume = rng.uniform(800_000.0, 1_200_000.0, n)
    index = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": close, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=index,
    )


def _short_df(n: int = 3) -> pd.DataFrame:
    close = np.array([100.0, 101.5, 103.0][:n])
    index = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "Open": close, "High": close + 1.0, "Low": close - 1.0, "Close": close,
            "Volume": np.full(n, 500_000.0),
        },
        index=index,
    )


class TestScoreSymbol:
    def test_none_on_empty_history(self):
        assert score_symbol("AAA", pd.DataFrame()) is None

    def test_uptrend_reads_as_uptrend(self):
        result = score_symbol("AAPL", _uptrend_df())
        assert isinstance(result, SymbolReport)
        assert result.symbol == "AAPL"
        assert result.price == pytest.approx(_uptrend_df()["Close"].iloc[-1], rel=1e-6)
        assert result.ema21_rising is True
        assert result.ema50_rising is True
        assert result.price_vs_sma50 == "ustunde"
        assert result.price_vs_sma200 == "ustunde"
        assert result.weekly_trend_aligned is True
        assert result.rsi_zone in {"asiri_alim", "notr", "asiri_satim"}
        assert isinstance(result.matched_long_groups, list)
        assert isinstance(result.matched_short_groups, list)
        assert "tahmin değil" in result.summary_tr

    def test_does_not_raise_on_insufficient_history(self):
        result = score_symbol("AAA", _short_df())
        assert isinstance(result, SymbolReport)
        # Not enough bars for any of these -- must degrade to None, not crash.
        assert result.ema21_rising is None
        assert result.price_vs_sma50 is None
        assert result.weekly_trend_aligned is None
        assert result.matched_long_groups == []
        assert result.matched_short_groups == []

    def test_serializes_as_a_keyed_object_not_a_positional_array(self):
        """Guards the dataclass-vs-NamedTuple trap in serialize.py directly:
        SymbolReport must stay a @dataclass so to_jsonable emits field names,
        not a positional list (see portfoy/serialize.py's module docstring).
        """
        result = score_symbol("AAPL", _uptrend_df())
        decoded = json.loads(dumps(result))
        assert isinstance(decoded, dict)
        assert decoded["symbol"] == "AAPL"
        assert isinstance(decoded["matched_long_groups"], list)
        assert "summary_tr" in decoded


class TestFibonacci:
    def test_fib_is_populated_for_a_symbol_with_enough_history(self):
        result = score_symbol("AAPL", _uptrend_df())
        assert result.fib is not None
        assert result.fib.swing_high > result.fib.swing_low
        assert result.fib.direction in {"yukselis", "dusus"}
        assert len(result.fib.levels) == len(config.FIB_RETRACEMENT_RATIOS) + len(
            config.FIB_EXTENSION_RATIOS
        )

    def test_fib_is_none_for_too_short_history(self):
        result = score_symbol("AAA", _short_df())
        assert result.fib is None

    def test_summary_tr_mentions_fibonacci_when_fib_is_present(self):
        result = score_symbol("AAPL", _uptrend_df())
        assert result.fib is not None
        assert "Fibonacci" in result.summary_tr

    def test_summary_tr_omits_fibonacci_sentence_when_fib_is_absent(self):
        result = score_symbol("AAA", _short_df())
        assert result.fib is None
        assert "Fibonacci" not in result.summary_tr


class TestCurrency:
    def test_bist_symbol_is_try(self):
        result = score_symbol("THYAO.IS", _uptrend_df())
        assert result.currency == "TRY"

    def test_us_symbol_is_usd(self):
        result = score_symbol("AAPL", _uptrend_df())
        assert result.currency == "USD"


def _raise_if_called(*_args, **_kwargs):
    raise AssertionError("network fetcher should not have been called for a BIST symbol")


class TestSymbolContext:
    def test_bist_symbol_short_circuits_without_any_network_call(self, monkeypatch):
        monkeypatch.setattr(report.data, "get_option_activity", _raise_if_called)
        monkeypatch.setattr(report.data, "get_ownership_flow", _raise_if_called)
        result = build_symbol_context("THYAO.IS")
        assert isinstance(result, SymbolContext)
        assert result.is_us is False
        assert result.unavailable_reason == "bist"
        assert result.put_call_ratio is None
        assert result.institutional_pct is None

    def test_us_symbol_computes_put_call_ratio_as_a_real_field(self, monkeypatch):
        activity = OptionActivity(
            symbol="AAPL", expiry="2026-09-18", call_volume=1000, put_volume=650,
            call_oi=5000, put_oi=3000,
        )
        monkeypatch.setattr(report.data, "get_option_activity", lambda symbol: activity)
        monkeypatch.setattr(report.data, "get_ownership_flow", lambda symbol: None)
        result = build_symbol_context("AAPL")
        assert result.is_us is True
        assert result.put_call_ratio == pytest.approx(0.65)
        assert result.pcr_mood == "bullish"  # 0.65 <= PCR_BULLISH=0.7
        assert result.call_volume == 1000
        assert result.put_volume == 650
        assert result.option_expiry == "2026-09-18"
        assert result.unavailable_reason is None

    def test_pcr_mood_bearish_boundary(self, monkeypatch):
        activity = OptionActivity(
            symbol="AAPL", expiry="2026-09-18", call_volume=100, put_volume=120,
            call_oi=0, put_oi=0,
        )
        monkeypatch.setattr(report.data, "get_option_activity", lambda symbol: activity)
        monkeypatch.setattr(report.data, "get_ownership_flow", lambda symbol: None)
        result = build_symbol_context("AAPL")
        assert result.put_call_ratio == pytest.approx(1.2)
        assert result.pcr_mood == "bearish"  # 1.2 >= PCR_BEARISH=1.0

    def test_us_symbol_surfaces_ownership_fields(self, monkeypatch):
        monkeypatch.setattr(report.data, "get_option_activity", lambda symbol: None)
        monkeypatch.setattr(
            report.data, "get_ownership_flow",
            lambda symbol: OwnershipFlow(institutional_pct=62.5, insider_net_pct_6m=-1.2),
        )
        result = build_symbol_context("MSFT")
        assert result.institutional_pct == pytest.approx(62.5)
        assert result.insider_net_pct_6m == pytest.approx(-1.2)
        assert result.unavailable_reason is None

    def test_us_symbol_with_no_data_from_either_fetcher(self, monkeypatch):
        monkeypatch.setattr(report.data, "get_option_activity", lambda symbol: None)
        monkeypatch.setattr(report.data, "get_ownership_flow", lambda symbol: None)
        result = build_symbol_context("ZZZZ")
        assert result.unavailable_reason == "no_data"
        assert result.put_call_ratio is None
        assert result.institutional_pct is None

    def test_serializes_as_a_keyed_object_with_put_call_ratio_present(self, monkeypatch):
        activity = OptionActivity(
            symbol="AAPL", expiry="2026-09-18", call_volume=1000, put_volume=650,
            call_oi=5000, put_oi=3000,
        )
        monkeypatch.setattr(report.data, "get_option_activity", lambda symbol: activity)
        monkeypatch.setattr(report.data, "get_ownership_flow", lambda symbol: None)
        result = build_symbol_context("AAPL")
        decoded = json.loads(dumps(result))
        assert isinstance(decoded, dict)
        # Regression guard: OptionActivity.put_call_ratio is a @property and is
        # silently dropped by serialize.py's dataclass-fields walk -- this must
        # be a real field on SymbolContext, not delegated to the property.
        assert decoded["put_call_ratio"] == pytest.approx(0.65)


class TestBuildReport:
    def test_none_when_history_is_empty(self, monkeypatch):
        monkeypatch.setattr(report.data, "get_history", lambda symbol, period=None: pd.DataFrame())
        assert build_report("ZZZZ") is None

    def test_delegates_to_score_symbol(self, monkeypatch):
        df = _uptrend_df()
        monkeypatch.setattr(report.data, "get_history", lambda symbol, period=None: df)
        result = build_report("AAPL")
        assert isinstance(result, SymbolReport)
        assert result.symbol == "AAPL"
