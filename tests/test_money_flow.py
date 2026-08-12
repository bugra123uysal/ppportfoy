import numpy as np
import pandas as pd
import pytest

from portfoy import money_flow
from portfoy.data import OwnershipFlow
from portfoy.money_flow import (
    MoneyFlowSignal,
    build_money_flow_scan,
    cmf_signal,
    obv_trend,
)

N = 40


def _frame(close: list[float]) -> pd.DataFrame:
    close = np.array(close, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(len(close), 1000.0),
        }
    )


class TestCmfSignal:
    def test_none_is_notr(self):
        assert cmf_signal(None) == "notr"

    def test_above_threshold_is_accumulation(self):
        assert cmf_signal(0.2) == "accumulation"

    def test_below_negative_threshold_is_distribution(self):
        assert cmf_signal(-0.2) == "distribution"

    def test_near_zero_is_notr(self):
        assert cmf_signal(0.01) == "notr"
        assert cmf_signal(-0.01) == "notr"


class TestObvTrend:
    def test_rising_series(self):
        obv = pd.Series(np.linspace(0, 1000, 30))
        assert obv_trend(obv) == "yukselis"

    def test_falling_series(self):
        obv = pd.Series(np.linspace(1000, 0, 30))
        assert obv_trend(obv) == "dusus"

    def test_flat_series(self):
        obv = pd.Series(np.full(30, 500.0))
        assert obv_trend(obv) == "yatay"

    def test_too_short_is_yatay(self):
        obv = pd.Series([1.0, 2.0, 3.0])
        assert obv_trend(obv) == "yatay"


class TestBuildMoneyFlowScan:
    def test_skips_symbols_with_insufficient_history(self, monkeypatch):
        monkeypatch.setattr(money_flow.data, "get_histories", lambda symbols, period=None: {})
        assert build_money_flow_scan({"AAA": "Test"}) == []

    def test_builds_signal_with_ownership_data(self, monkeypatch):
        close = np.array([100.0 + i * 0.5 for i in range(N)])
        # Close sits near the top of each bar's range -> CMF accumulation.
        df = pd.DataFrame(
            {
                "Open": close - 1.0,
                "High": close + 0.2,
                "Low": close - 2.0,
                "Close": close,
                "Volume": np.full(N, 1000.0),
            }
        )
        monkeypatch.setattr(
            money_flow.data, "get_histories", lambda symbols, period=None: {"AAA": df}
        )
        monkeypatch.setattr(
            money_flow.data, "get_ownership_flow",
            lambda sym: OwnershipFlow(institutional_pct=62.5, insider_net_pct_6m=1.2),
        )

        out = build_money_flow_scan({"AAA": "Enerji"})
        assert len(out) == 1
        signal = out[0]
        assert isinstance(signal, MoneyFlowSignal)
        assert signal.symbol == "AAA"
        assert signal.sector == "Enerji"
        assert signal.price == pytest.approx(close[-1])
        assert signal.institutional_pct == pytest.approx(62.5)
        assert signal.insider_net_pct_6m == pytest.approx(1.2)
        # Every bar closes near the high of its own range -> accumulation.
        assert signal.cmf_signal == "accumulation"
        assert signal.cmf is not None and signal.cmf > 0
        assert signal.obv_trend == "yukselis"

    def test_missing_ownership_data_yields_none_fields(self, monkeypatch):
        df = _frame([100.0] * N)
        monkeypatch.setattr(
            money_flow.data, "get_histories", lambda symbols, period=None: {"AAA": df}
        )
        monkeypatch.setattr(money_flow.data, "get_ownership_flow", lambda sym: None)

        out = build_money_flow_scan({"AAA": "Enerji"})
        assert out[0].institutional_pct is None
        assert out[0].insider_net_pct_6m is None
