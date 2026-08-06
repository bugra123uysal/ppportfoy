import pandas as pd

from portfoy import position_health
from portfoy.data import FundamentalMetrics
from portfoy.money_flow import MoneyFlowSignal
from portfoy.position_health import evaluate_portfolio, evaluate_position
from portfoy.trade_scan import TradeSignal

_DF = pd.DataFrame({"Close": [100.0, 101.0]})


def _short_signal(groups: list[int]) -> TradeSignal:
    return TradeSignal(
        symbol="AAA", sector="", price=100.0, change_1d=0.0, direction="short",
        groups=groups, atr_14=2.0, suggested_stop=104.0,
        pct_from_52w_high=-10.0, pct_from_52w_low=5.0, weekly_trend_aligned=True,
    )


def _long_signal(groups: list[int]) -> TradeSignal:
    return TradeSignal(
        symbol="AAA", sector="", price=100.0, change_1d=0.0, direction="long",
        groups=groups, atr_14=2.0, suggested_stop=96.0,
        pct_from_52w_high=-10.0, pct_from_52w_low=5.0, weekly_trend_aligned=True,
    )


def _money_flow(cmf_signal: str) -> MoneyFlowSignal:
    return MoneyFlowSignal(
        symbol="AAA", sector="", price=100.0, change_1d=0.0, cmf=0.1,
        cmf_signal=cmf_signal, mfi=50.0, obv_trend="yatay",
        institutional_pct=None, insider_net_pct_6m=None,
    )


def _fundamentals(peg: float | None, ev_ebitda: float | None = None) -> FundamentalMetrics:
    return FundamentalMetrics(
        pe=20.0, peg=peg, ev_ebitda=ev_ebitda, revenue_growth=10.0,
        gross_margin=40.0, operating_margin=15.0, roe=20.0,
        debt_to_equity=0.5, fcf_yield=3.0,
    )


class TestEvaluatePosition:
    def test_empty_history_returns_none(self):
        assert evaluate_position("AAA", pd.DataFrame()) is None

    def test_no_signals_is_neutral(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_position("AAA", _DF)
        assert out.score == 0
        assert out.verdict == "notr"
        assert out.reasons == []

    def test_short_technical_signal_lowers_score(self, monkeypatch):
        monkeypatch.setattr(
            position_health, "trade_scan_symbol", lambda sym, sector, df: [_short_signal([1, 3])]
        )
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_position("AAA", _DF)
        assert out.score == -1
        assert "teknik satış" in out.reasons[0]

    def test_long_signals_are_ignored_not_treated_as_bullish(self, monkeypatch):
        # evaluate_position only reads short-direction signals -- a long
        # match says nothing about whether an *existing* holding is weakening.
        monkeypatch.setattr(
            position_health, "trade_scan_symbol", lambda sym, sector, df: [_long_signal([1])]
        )
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_position("AAA", _DF)
        assert out.score == 0
        assert out.reasons == []

    def test_distribution_money_flow_lowers_score(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(
            position_health, "money_flow_scan_symbol",
            lambda sym, sector, df: _money_flow("distribution"),
        )
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_position("AAA", _DF)
        assert out.score == -1
        assert "dağıtım" in out.reasons[0]

    def test_accumulation_money_flow_is_not_penalized(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(
            position_health, "money_flow_scan_symbol",
            lambda sym, sector, df: _money_flow("accumulation"),
        )
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_position("AAA", _DF)
        assert out.score == 0

    def test_expensive_valuation_lowers_score(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(
            position_health.data, "get_fundamentals",
            lambda sym: _fundamentals(peg=3.0, ev_ebitda=20.0),
        )
        out = evaluate_position("AAA", _DF)
        assert out.score == -1
        assert "pahalı" in out.reasons[0]

    def test_cheap_valuation_raises_score(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(
            position_health.data, "get_fundamentals",
            lambda sym: _fundamentals(peg=0.5, ev_ebitda=8.0),
        )
        out = evaluate_position("AAA", _DF)
        assert out.score == 1

    def test_combined_negative_signals_reach_weakening_verdict(self, monkeypatch):
        monkeypatch.setattr(
            position_health, "trade_scan_symbol", lambda sym, sector, df: [_short_signal([1])]
        )
        monkeypatch.setattr(
            position_health, "money_flow_scan_symbol",
            lambda sym, sector, df: _money_flow("distribution"),
        )
        monkeypatch.setattr(
            position_health.data, "get_fundamentals",
            lambda sym: _fundamentals(peg=3.0, ev_ebitda=20.0),
        )
        out = evaluate_position("AAA", _DF)
        assert out.score == -3
        assert out.verdict == "zayifliyor"
        assert len(out.reasons) == 3


class TestEvaluatePortfolio:
    def test_skips_symbols_with_no_history(self, monkeypatch):
        monkeypatch.setattr(position_health, "trade_scan_symbol", lambda sym, sector, df: [])
        monkeypatch.setattr(position_health, "money_flow_scan_symbol", lambda sym, sector, df: None)
        monkeypatch.setattr(position_health.data, "get_fundamentals", lambda sym: None)
        out = evaluate_portfolio(["AAA", "BBB"], {"AAA": _DF})
        assert [h.symbol for h in out] == ["AAA"]
