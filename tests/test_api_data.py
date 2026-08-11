"""api_data mirrors app.build_context / the views' data chains for the JSON
API. These tests mock the data.py/storage.py/news.py boundary so nothing
here touches the network -- only the wiring (which function calls which,
in what order, with what arguments) is under test.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from portfoy import api_data, config
from portfoy.data import AnalystView, Quote
from portfoy.money_flow import MoneyFlowSignal
from portfoy.options import OptionActivity
from portfoy.storage import CashHolding, Position
from portfoy.trade_scan import TradeSignal
from portfoy.vcp_scan import VcpCandidate

AAPL = Position(symbol="AAPL", quantity=10.0, avg_cost=100.0, currency="USD",
                 added="2026-01-01", notes="")
THYAO = Position(symbol="THYAO.IS", quantity=50.0, avg_cost=200.0, currency="TRY",
                  added="2026-01-01", notes="")


def _history(prices: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=len(prices), freq="D")
    return pd.DataFrame(
        {"Open": prices, "High": prices, "Low": prices, "Close": prices}, index=idx
    )


@pytest.fixture
def stub_portfolio(monkeypatch):
    monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL, THYAO])
    monkeypatch.setattr(
        api_data.storage, "load_cash",
        lambda: [CashHolding(currency="USD", amount=500.0)],
    )
    monkeypatch.setattr(
        api_data.data, "get_quotes",
        lambda symbols: {
            "AAPL": Quote("AAPL", 110.0, 108.0, 1.5),
            "THYAO.IS": Quote("THYAO.IS", 210.0, 205.0, 2.0),
        },
    )
    monkeypatch.setattr(
        api_data.data, "get_histories",
        lambda symbols, period=None: {sym: _history([100, 110]) for sym in symbols},
    )
    monkeypatch.setattr(api_data.data, "get_usdtry", lambda: 30.0)
    # position_health.evaluate_portfolio (invoked from portfolio_summary_payload)
    # calls this per held symbol -- stub it so no test here hits the network.
    monkeypatch.setattr(api_data.data, "get_fundamentals", lambda sym: None)


class TestPositionsPayload:
    def test_returns_metrics_cash_and_fx(self, stub_portfolio):
        out = api_data.positions_payload()
        assert {m.symbol for m in out["metrics"]} == {"AAPL", "THYAO.IS"}
        assert out["cash"][0].currency == "USD"
        assert out["usdtry"] == 30.0

    def test_empty_portfolio_yields_no_metrics(self, monkeypatch):
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [])
        monkeypatch.setattr(api_data.storage, "load_cash", lambda: [])
        monkeypatch.setattr(api_data.data, "get_usdtry", lambda: 30.0)
        out = api_data.positions_payload()
        assert out["metrics"] == []


class TestPortfolioSummaryPayload:
    def test_includes_totals_and_alerts(self, stub_portfolio, monkeypatch):
        monkeypatch.setattr(
            api_data.data, "get_macro_snapshot",
            lambda: [{"symbol": "^VIX", "label": "VIX", "price": 15.0, "change_pct": 0.0}],
        )
        monkeypatch.setattr(api_data.data, "get_next_earnings", lambda sym: None)
        out = api_data.portfolio_summary_payload()
        assert "value_usd" in out["totals"]
        assert isinstance(out["alerts"], list)

    def test_vix_missing_from_macro_is_handled(self, stub_portfolio, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_macro_snapshot", lambda: [])
        monkeypatch.setattr(api_data.data, "get_next_earnings", lambda sym: None)
        out = api_data.portfolio_summary_payload()
        assert isinstance(out["alerts"], list)

    def test_includes_position_health_for_every_holding(self, stub_portfolio, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_macro_snapshot", lambda: [])
        monkeypatch.setattr(api_data.data, "get_next_earnings", lambda sym: None)
        out = api_data.portfolio_summary_payload()
        assert {h.symbol for h in out["position_health"]} == {"AAPL", "THYAO.IS"}


class TestPortfolioHistoryPayload:
    def test_delegates_to_storage(self, monkeypatch):
        monkeypatch.setattr(
            api_data.storage, "load_history",
            lambda: [{"date": "2026-01-01", "value_try": 1.0, "value_usd": 1.0}],
        )
        assert api_data.portfolio_history_payload() == [
            {"date": "2026-01-01", "value_try": 1.0, "value_usd": 1.0}
        ]


class TestRotationPayload:
    def test_empty_closes_returns_empty_shape(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda symbols: pd.DataFrame())
        assert api_data.rotation_payload() == {"sectors": [], "leaders": {}}

    def test_include_mine_adds_us_holdings_only(self, monkeypatch):
        captured = {}

        def fake_weekly(symbols):
            captured["symbols"] = symbols
            return pd.DataFrame()

        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL, THYAO])
        monkeypatch.setattr(api_data.data, "get_weekly_closes", fake_weekly)
        api_data.rotation_payload(include_mine=True)
        assert "AAPL" in captured["symbols"]
        assert "THYAO.IS" not in captured["symbols"]

    def test_returns_sectors_and_leaders(self, monkeypatch):
        idx = pd.date_range("2023-01-01", periods=160, freq="W")
        symbols = [config.RRG_BENCHMARK, *config.SECTOR_ETFS]
        leader_symbols = [s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks]
        data_cols = {sym: pd.Series(range(160), index=idx, dtype=float) + 100.0
                     for sym in dict.fromkeys([*symbols, *leader_symbols])}
        closes = pd.DataFrame(data_cols)
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda syms: closes)
        out = api_data.rotation_payload()
        assert isinstance(out["sectors"], list)
        assert set(out["leaders"]) == set(config.SECTOR_LEADER_STOCKS)


class TestRotationOverlapPayload:
    def test_empty_closes_returns_empty_candidates(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda symbols: pd.DataFrame())
        assert api_data.rotation_overlap_payload() == {"candidates": []}

    def test_runs_all_three_my_trade_scans_over_the_full_universe(self, monkeypatch):
        idx = pd.date_range("2023-01-01", periods=160, freq="W")
        symbols = [config.RRG_BENCHMARK, *config.SECTOR_ETFS]
        leader_symbols = [s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks]
        data_cols = {sym: pd.Series(range(160), index=idx, dtype=float) + 100.0
                     for sym in dict.fromkeys([*symbols, *leader_symbols])}
        closes = pd.DataFrame(data_cols)
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda syms: closes)

        # Every symbol shares the identical price series above, so every
        # sector lands in the same RRG quadrant and every XLK leader (AAPL,
        # MSFT, NVDA -- the pool's first three, tied on perf so ranked by
        # config order) is a rotation candidate. One real, distinguishable
        # signal per scan (rather than all three returning []) proves each
        # scan's result reaches build_rotation_overlap through the right
        # positional argument -- a swap between two of the three would
        # either surface the wrong signal label below or raise
        # AttributeError (the three signal dataclasses don't share fields).
        captured: dict[str, set] = {}

        def fake_trade_scan(universe):
            captured["trade_scan"] = set(universe)
            return [TradeSignal(
                symbol="AAPL", sector="Teknoloji", price=200.0, change_1d=1.0,
                direction="long", groups=[1], atr_14=2.0, suggested_stop=195.0,
                pct_from_52w_high=-5.0, pct_from_52w_low=20.0, weekly_trend_aligned=True,
            )]

        def fake_vcp_scan(universe):
            captured["vcp"] = set(universe)
            return [VcpCandidate(
                symbol="MSFT", sector="Teknoloji", price=400.0, change_1d=1.0, adr_pct=4.0,
                trailing_return_pct=20.0, range_contraction_pct=50.0,
                volume_contraction_pct=60.0, pct_from_52w_high=-5.0, suggested_stop=390.0,
            )]

        def fake_money_flow_scan(universe):
            captured["money_flow"] = set(universe)
            return [MoneyFlowSignal(
                symbol="NVDA", sector="Teknoloji", price=120.0, change_1d=1.0, cmf=0.2,
                cmf_signal="accumulation", mfi=55.0, obv_trend="yukselis",
                institutional_pct=80.0, insider_net_pct_6m=1.0,
            )]

        monkeypatch.setattr(api_data, "build_trade_scan", fake_trade_scan)
        monkeypatch.setattr(api_data, "build_vcp_scan", fake_vcp_scan)
        monkeypatch.setattr(api_data, "build_money_flow_scan", fake_money_flow_scan)
        out = api_data.rotation_overlap_payload()

        all_stocks = {s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks}
        assert captured["trade_scan"] == all_stocks
        assert captured["vcp"] == all_stocks
        assert captured["money_flow"] == all_stocks

        by_symbol = {c.symbol: c for c in out["candidates"]}
        assert by_symbol["AAPL"].signals == ("trade_scan_long",)
        assert by_symbol["MSFT"].signals == ("vcp",)
        assert by_symbol["NVDA"].signals == ("money_flow_accumulation",)


class TestTradeScanPayload:
    def test_empty_history_yields_no_signals(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_histories", lambda symbols, period=None: {})
        assert api_data.trade_scan_payload() == {"signals": []}

    def test_universe_covers_every_sector_leader_stock(self, monkeypatch):
        captured = {}

        def fake_histories(symbols, period=None):
            captured.update({sym: True for sym in symbols})
            return {}

        monkeypatch.setattr(api_data.data, "get_histories", fake_histories)
        api_data.trade_scan_payload()
        all_stocks = {s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks}
        assert set(captured) == all_stocks


class TestMoneyFlowPayload:
    def test_empty_history_yields_no_signals(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_histories", lambda symbols, period=None: {})
        assert api_data.money_flow_payload() == {"signals": []}

    def test_universe_covers_every_sector_leader_stock(self, monkeypatch):
        captured = {}

        def fake_histories(symbols, period=None):
            captured.update({sym: True for sym in symbols})
            return {}

        monkeypatch.setattr(api_data.data, "get_histories", fake_histories)
        api_data.money_flow_payload()
        all_stocks = {s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks}
        assert set(captured) == all_stocks


class TestFundamentalScanPayload:
    def test_no_data_yields_no_signals(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_fundamentals", lambda sym: None)
        assert api_data.fundamental_scan_payload() == {"signals": []}

    def test_universe_covers_every_sector_leader_stock(self, monkeypatch):
        captured = {}

        def fake_fundamentals(sym):
            captured[sym] = True
            return None

        monkeypatch.setattr(api_data.data, "get_fundamentals", fake_fundamentals)
        api_data.fundamental_scan_payload()
        all_stocks = {s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks}
        assert set(captured) == all_stocks


class TestOptionsPayloads:
    def test_option_activity_payload_delegates(self, monkeypatch):
        activity = OptionActivity(symbol="SPY", expiry="2026-08-15", call_volume=1,
                                    put_volume=1, call_oi=1, put_oi=1)
        monkeypatch.setattr(api_data.data, "get_option_activity", lambda sym: activity)
        assert api_data.option_activity_payload("SPY") is activity

    def test_scan_ranks_by_volume_and_drops_none(self, monkeypatch):
        busy = OptionActivity(symbol="SPY", expiry="x", call_volume=100, put_volume=50,
                                call_oi=1, put_oi=1)
        quiet = OptionActivity(symbol="QQQ", expiry="x", call_volume=1, put_volume=0,
                                 call_oi=1, put_oi=1)

        def fake_activity(sym):
            return {"SPY": busy, "QQQ": quiet}.get(sym)

        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [])
        monkeypatch.setattr(api_data.data, "get_option_activity", fake_activity)
        out = api_data.options_scan_payload()
        assert [a.symbol for a in out][:1] == ["SPY"]


class TestBreadthAndSentiment:
    def test_breadth_none_on_empty_closes(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_daily_closes", lambda symbols: pd.DataFrame())
        assert api_data.breadth_payload() is None

    def test_sentiment_composes_from_available_inputs(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_macro_snapshot",
                             lambda: [{"symbol": "^VIX", "label": "VIX", "price": 15.0,
                                       "change_pct": 0.0}])
        monkeypatch.setattr(api_data.data, "get_history", lambda sym: pd.DataFrame())
        monkeypatch.setattr(api_data.data, "get_option_activity", lambda sym: None)
        monkeypatch.setattr(api_data.data, "get_daily_closes", lambda symbols: pd.DataFrame())
        score = api_data.sentiment_payload()
        assert score is not None
        assert "vix" in score.components


class TestMacroPayload:
    def test_delegates_to_data(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_macro_snapshot", lambda: [{"symbol": "^VIX"}])
        assert api_data.macro_payload() == [{"symbol": "^VIX"}]


class TestYieldCurvePayload:
    def test_computes_spread_and_inversion(self, monkeypatch):
        monkeypatch.setattr(
            api_data.data, "get_quotes",
            lambda symbols: {
                config.YIELD_10Y_TICKER: Quote(config.YIELD_10Y_TICKER, 4.0, 4.0, 0.0),
                config.YIELD_3M_TICKER: Quote(config.YIELD_3M_TICKER, 5.0, 5.0, 0.0),
            },
        )
        monkeypatch.setattr(api_data.data, "get_history", lambda sym, period=None: pd.DataFrame())
        snap = api_data.yield_curve_payload()
        assert snap.yield_10y == pytest.approx(4.0)
        assert snap.yield_3m == pytest.approx(5.0)
        assert snap.spread_10y_3m == pytest.approx(-1.0)
        assert snap.inverted is True
        assert snap.credit_spread_proxy_change is None

    def test_missing_quotes_still_returns_snapshot(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_quotes", lambda symbols: {})
        monkeypatch.setattr(api_data.data, "get_history", lambda sym, period=None: pd.DataFrame())
        snap = api_data.yield_curve_payload()
        assert snap.spread_10y_3m is None
        assert snap.inverted is False


class TestAnalystPayload:
    def test_only_us_symbols_are_queried(self, monkeypatch):
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL, THYAO])
        queried: list[str] = []

        def fake_view(sym):
            queried.append(sym)
            return AnalystView(300.0, 350.0, 250.0, "al", 20)

        monkeypatch.setattr(api_data.data, "get_analyst_view", fake_view)
        out = api_data.analyst_payload()
        assert queried == ["AAPL"]
        assert out == {"AAPL": AnalystView(300.0, 350.0, 250.0, "al", 20)}

    def test_symbols_with_no_view_are_omitted(self, monkeypatch):
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL])
        monkeypatch.setattr(api_data.data, "get_analyst_view", lambda sym: None)
        assert api_data.analyst_payload() == {}


class TestCalendarPayload:
    def test_includes_earnings_for_non_bist_holdings(self, monkeypatch):
        soon = date.today() + timedelta(days=3)
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL, THYAO])
        monkeypatch.setattr(
            api_data.data, "get_next_earnings",
            lambda sym: soon if sym == "AAPL" else None,
        )
        events = api_data.calendar_payload(days=10)
        assert any(e.kind == "earnings" and e.symbol == "AAPL" for e in events)
        assert all(e.symbol != "THYAO.IS" for e in events)


class TestVcpScanPayload:
    def test_empty_history_yields_no_candidates(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_histories", lambda symbols, period=None: {})
        assert api_data.vcp_scan_payload() == {"candidates": []}

    def test_universe_covers_every_sector_leader_stock(self, monkeypatch):
        captured = {}

        def fake_histories(symbols, period=None):
            captured.update({sym: True for sym in symbols})
            return {}

        monkeypatch.setattr(api_data.data, "get_histories", fake_histories)
        api_data.vcp_scan_payload()
        all_stocks = {s for stocks in config.SECTOR_LEADER_STOCKS.values() for s in stocks}
        assert set(captured) == all_stocks


def _unexpected_rescan():
    raise AssertionError("build_movers_scan should not run when a snapshot is already persisted")


class TestMoversPayload:
    def test_returns_persisted_snapshot_without_rescanning(self, monkeypatch):
        snapshot = {"generated_at": "2026-01-01T00:00:00+00:00", "gainers": [], "volume_spikes": []}
        monkeypatch.setattr(api_data, "load_snapshot", lambda: snapshot)
        monkeypatch.setattr(api_data, "build_movers_scan", _unexpected_rescan)
        assert api_data.movers_payload() == snapshot

    def test_falls_back_to_a_fresh_scan_when_nothing_persisted(self, monkeypatch):
        from portfoy.movers import MoversScan

        scan = MoversScan(generated_at="2026-01-01T00:00:00+00:00", gainers=[], volume_spikes=[])
        monkeypatch.setattr(api_data, "load_snapshot", lambda: None)
        monkeypatch.setattr(api_data, "build_movers_scan", lambda: scan)
        assert api_data.movers_payload() is scan


class TestNewsPayload:
    def test_delegates_to_news_module(self, monkeypatch):
        from portfoy import news

        monkeypatch.setattr(news, "get_news_for", lambda sym, lang: [{"symbol": sym}])
        assert api_data.news_payload("AAPL", "tr") == [{"symbol": "AAPL"}]


class TestComparePayload:
    def test_try_base_without_fx_history_returns_empty(self, stub_portfolio, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_histories", lambda symbols, period=None: {})
        out = api_data.compare_payload(base="TRY")
        assert out == []

    def test_usd_base_produces_portfolio_series(self, stub_portfolio, monkeypatch):
        prices = _history([100.0, 105.0, 110.0])

        def fake_histories(symbols, period=None):
            return {sym: prices for sym in symbols}

        monkeypatch.setattr(api_data.data, "get_histories", fake_histories)
        out = api_data.compare_payload(base="USD")
        assert any(r.key == "portfolio" for r in out)
