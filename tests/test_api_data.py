"""api_data mirrors app.build_context / the views' data chains for the JSON
API. These tests mock the data.py/storage.py/news.py boundary so nothing
here touches the network -- only the wiring (which function calls which,
in what order, with what arguments) is under test.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from portfoy import api_data
from portfoy.data import Quote
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
    monkeypatch.setattr(api_data.data, "get_history", lambda sym, period=None: _history([100, 110]))
    monkeypatch.setattr(api_data.data, "get_usdtry", lambda: 30.0)


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
    def test_empty_closes_returns_empty_list(self, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_weekly_closes", lambda symbols: pd.DataFrame())
        assert api_data.rotation_payload() == []

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


class TestNewsPayload:
    def test_delegates_to_news_module(self, monkeypatch):
        from portfoy import news

        monkeypatch.setattr(news, "get_news_for", lambda sym, lang: [{"symbol": sym}])
        assert api_data.news_payload("AAPL", "tr") == [{"symbol": "AAPL"}]


class TestComparePayload:
    def test_try_base_without_fx_history_returns_empty(self, stub_portfolio, monkeypatch):
        monkeypatch.setattr(api_data.data, "get_history",
                             lambda sym, period=None: pd.DataFrame())
        out = api_data.compare_payload(base="TRY")
        assert out == []

    def test_usd_base_produces_portfolio_series(self, stub_portfolio, monkeypatch):
        prices = _history([100.0, 105.0, 110.0])

        def fake_history(sym, period=None):
            return prices

        monkeypatch.setattr(api_data.data, "get_history", fake_history)
        out = api_data.compare_payload(base="USD")
        assert any(r.key == "portfolio" for r in out)
