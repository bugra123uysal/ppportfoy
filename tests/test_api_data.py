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
from portfoy.options import OptionActivity
from portfoy.storage import CashHolding, Position

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


class TestStagePayload:
    def test_empty_portfolio_skips_history_fetch(self, monkeypatch):
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [])

        def _raise_if_called(symbols, period=None):
            raise AssertionError("get_histories should not run for an empty portfolio")

        monkeypatch.setattr(api_data.data, "get_histories", _raise_if_called)
        assert api_data.stage_payload() == {"stages": [], "commentary": None}

    def test_fetches_holdings_and_benchmarks_with_the_stage_period(self, monkeypatch):
        captured = []
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL, THYAO])

        def fake_histories(symbols, period=None):
            captured.append((set(symbols), period))
            return {}

        monkeypatch.setattr(api_data.data, "get_histories", fake_histories)
        api_data.stage_payload()

        holdings_call, benchmark_call = captured
        assert holdings_call == ({"AAPL", "THYAO.IS"}, config.STAGE_ANALYSIS_PERIOD)
        assert benchmark_call == (
            set(config.STAGE_BENCHMARKS.values()), config.STAGE_ANALYSIS_PERIOD,
        )

    def test_commentary_is_wired_from_the_scan_result(self, monkeypatch):
        uptrend = _history([100.0 + i * 0.5 for i in range(800)])
        monkeypatch.setattr(api_data.storage, "load_portfolio", lambda: [AAPL])
        monkeypatch.setattr(
            api_data.data, "get_histories",
            lambda symbols, period=None: {"AAPL": uptrend} if "AAPL" in symbols else {},
        )
        captured = {}
        monkeypatch.setattr(
            api_data, "stage_commentary",
            lambda stages: captured.update(stages=stages) or "yorum",
        )
        out = api_data.stage_payload()
        assert out["commentary"] == "yorum"
        assert [s.symbol for s in out["stages"]] == ["AAPL"]
        assert captured["stages"] == out["stages"]


class TestRotationPayload:
    def test_empty_closes_returns_empty_shape(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda symbols: pd.DataFrame())
        assert api_data.rotation_payload() == {"sectors": [], "leaders": {}, "commentary": None}

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


class TestReportPayload:
    def test_returns_report_and_context_for_a_known_symbol(self, monkeypatch):
        report_sentinel = object()
        context_sentinel = object()
        monkeypatch.setattr(api_data, "build_report", lambda symbol: report_sentinel)
        monkeypatch.setattr(api_data, "build_symbol_context", lambda symbol: context_sentinel)
        monkeypatch.setattr(
            api_data, "symbol_report_commentary", lambda report, context: "yorum"
        )
        result = api_data.report_payload("AAPL")
        assert result == {
            "report": report_sentinel, "context": context_sentinel, "commentary": "yorum",
        }

    def test_none_report_skips_context_entirely(self, monkeypatch):
        def _raise_if_called(symbol):
            raise AssertionError("build_symbol_context should not run for an unknown symbol")

        def _raise_if_commentary_called(report, context):
            raise AssertionError("commentary should not run for an unknown symbol")

        monkeypatch.setattr(api_data, "build_report", lambda symbol: None)
        monkeypatch.setattr(api_data, "build_symbol_context", _raise_if_called)
        monkeypatch.setattr(api_data, "symbol_report_commentary", _raise_if_commentary_called)
        result = api_data.report_payload("ZZZZ")
        assert result == {"report": None, "context": None, "commentary": None}


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


class TestMarketPulsePayload:
    def test_reuses_the_pages_own_breadth_sentiment_yield_curve_macro(self, monkeypatch):
        """market_pulse_payload must reuse the exact same payload functions
        Piyasa Pusulası's other panels already call, not a parallel fetch
        path -- otherwise the digest could disagree with the numbers shown
        right next to it."""
        sentinel_breadth, sentinel_sentiment = object(), object()
        sentinel_yield_curve, sentinel_macro = object(), [{"symbol": "^GSPC"}]
        monkeypatch.setattr(api_data, "breadth_payload", lambda: sentinel_breadth)
        monkeypatch.setattr(api_data, "sentiment_payload", lambda: sentinel_sentiment)
        monkeypatch.setattr(api_data, "yield_curve_payload", lambda: sentinel_yield_curve)
        monkeypatch.setattr(api_data, "macro_payload", lambda: sentinel_macro)
        captured = {}
        monkeypatch.setattr(
            api_data, "market_pulse_commentary",
            lambda breadth, sentiment, yield_curve, macro: captured.update(
                breadth=breadth, sentiment=sentiment, yield_curve=yield_curve, macro=macro
            ) or "yorum",
        )
        assert api_data.market_pulse_payload() == {"commentary": "yorum"}
        assert captured == {
            "breadth": sentinel_breadth, "sentiment": sentinel_sentiment,
            "yield_curve": sentinel_yield_curve, "macro": sentinel_macro,
        }


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
