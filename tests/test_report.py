import json

import numpy as np
import pandas as pd
import pytest

from portfoy import report
from portfoy.report import SymbolReport, build_report, score_symbol
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
