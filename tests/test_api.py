"""Flask route wiring for the read-only Vercel API (api/index.py).

api_data's own logic is covered by test_api_data.py. These tests only check:
auth enforcement (the API exposes personal portfolio data, so this matters),
each route calling the right api_data function with the right arguments, and
error shaping (input validation -> 400, unhandled exceptions -> JSON 500,
never a leaked traceback).

api/ isn't a Python package (Vercel expects a plain file per function), so
the module is loaded from its file path instead of being importable normally.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_API_DIR = Path(__file__).resolve().parent.parent / "api"
_spec = importlib.util.spec_from_file_location("_portfoy_api_index", _API_DIR / "index.py")
api_index = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = api_index
_spec.loader.exec_module(api_index)

API_KEY = "s3cr3t-test-key"
AUTH = {"X-API-Key": API_KEY}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("PORTFOY_API_KEY", API_KEY)
    return api_index.app.test_client()


class TestAuth:
    def test_missing_key_is_401(self, client):
        assert client.get("/api/market/macro").status_code == 401

    def test_wrong_key_is_401(self, client):
        resp = client.get("/api/market/macro", headers={"X-API-Key": "nope"})
        assert resp.status_code == 401

    def test_correct_header_key_authorizes(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "macro_payload", lambda: [])
        assert client.get("/api/market/macro", headers=AUTH).status_code == 200

    def test_query_param_key_alone_does_not_authorize(self, client):
        """Header only, deliberately -- see api/index.py's _authorized docstring."""
        resp = client.get(f"/api/market/macro?api_key={API_KEY}")
        assert resp.status_code == 401

    def test_unconfigured_key_fails_closed(self, client, monkeypatch):
        monkeypatch.delenv("PORTFOY_API_KEY", raising=False)
        assert client.get("/api/market/macro", headers=AUTH).status_code == 401

    def test_unauthorized_body_is_json(self, client):
        resp = client.get("/api/market/macro")
        assert resp.get_json() == {"error": "unauthorized"}


class TestRouteWiring:
    def test_positions(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "positions_payload",
                             lambda: {"metrics": [], "cash": [], "usdtry": 30.0})
        resp = client.get("/api/positions", headers=AUTH)
        assert resp.get_json() == {"metrics": [], "cash": [], "usdtry": 30.0}

    def test_portfolio_summary(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "portfolio_summary_payload",
                             lambda: {"totals": {}, "alerts": []})
        resp = client.get("/api/portfolio/summary", headers=AUTH)
        assert resp.get_json() == {"totals": {}, "alerts": []}

    def test_portfolio_history(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "portfolio_history_payload", lambda: [{"a": 1}])
        resp = client.get("/api/portfolio/history", headers=AUTH)
        assert resp.get_json() == [{"a": 1}]

    def test_rotation_default_excludes_mine(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "rotation_payload",
                             lambda include_mine=False: captured.setdefault("v", include_mine))
        client.get("/api/rotation", headers=AUTH)
        assert captured["v"] is False

    def test_rotation_include_mine_true(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "rotation_payload",
                             lambda include_mine=False: captured.setdefault("v", include_mine))
        client.get("/api/rotation?include_mine=true", headers=AUTH)
        assert captured["v"] is True

    def test_options_scan(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "options_scan_payload", lambda: [])
        assert client.get("/api/options", headers=AUTH).status_code == 200

    def test_fundamentals(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "fundamental_scan_payload", lambda: {"signals": []})
        resp = client.get("/api/fundamentals", headers=AUTH)
        assert resp.get_json() == {"signals": []}

    def test_vcp_scan(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "vcp_scan_payload", lambda: {"candidates": []})
        resp = client.get("/api/vcp-scan", headers=AUTH)
        assert resp.get_json() == {"candidates": []}

    def test_rotation_overlap(self, client, monkeypatch):
        monkeypatch.setattr(
            api_index.api_data, "rotation_overlap_payload", lambda: {"candidates": []}
        )
        resp = client.get("/api/rotation-overlap", headers=AUTH)
        assert resp.get_json() == {"candidates": []}

    def test_option_activity_passes_normalized_symbol(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "option_activity_payload",
                             lambda sym: captured.setdefault("sym", sym))
        client.get("/api/options/aapl", headers=AUTH)
        assert captured["sym"] == "AAPL"

    def test_option_activity_rejects_invalid_symbol(self, client):
        resp = client.get("/api/options/%3Cscript%3E", headers=AUTH)
        assert resp.status_code == 400

    def test_market_breadth(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "breadth_payload", lambda: None)
        resp = client.get("/api/market/breadth", headers=AUTH)
        assert resp.get_json() is None
        assert resp.status_code == 200

    def test_movers(self, client, monkeypatch):
        payload = {"generated_at": "2026-01-01T00:00:00+00:00", "gainers": [], "volume_spikes": []}
        monkeypatch.setattr(api_index.api_data, "movers_payload", lambda: payload)
        resp = client.get("/api/movers", headers=AUTH)
        assert resp.get_json() == payload

    def test_movers_scan_delegates_to_scan_if_due(self, client, monkeypatch):
        from portfoy.movers import MoversScan

        scan = MoversScan(generated_at="2026-01-01T00:00:00+00:00", gainers=[], volume_spikes=[])
        monkeypatch.setattr(api_index.movers_module, "scan_if_due", lambda: scan)
        resp = client.post("/api/movers/scan", headers=AUTH)
        assert resp.status_code == 200
        assert resp.get_json()["generated_at"] == "2026-01-01T00:00:00+00:00"

    def test_movers_scan_requires_auth(self, client):
        assert client.post("/api/movers/scan").status_code == 401

    def test_market_sentiment(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "sentiment_payload", lambda: None)
        assert client.get("/api/market/sentiment", headers=AUTH).status_code == 200

    def test_market_macro(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "macro_payload", lambda: [{"symbol": "^VIX"}])
        resp = client.get("/api/market/macro", headers=AUTH)
        assert resp.get_json() == [{"symbol": "^VIX"}]

    def test_market_yield_curve(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "yield_curve_payload", lambda: {"inverted": False})
        resp = client.get("/api/market/yield-curve", headers=AUTH)
        assert resp.get_json() == {"inverted": False}

    def test_analyst(self, client, monkeypatch):
        payload = {"AAPL": {"consensus": "al"}}
        monkeypatch.setattr(api_index.api_data, "analyst_payload", lambda: payload)
        resp = client.get("/api/analyst", headers=AUTH)
        assert resp.get_json() == payload

    def test_analyst_serializes_as_object_not_array(self, client, monkeypatch):
        """Exercises the real serialization path (unlike test_analyst above,
        which mocks analyst_payload itself) -- AnalystView is a NamedTuple,
        which without portfoy.serialize's dedicated branch silently
        serializes as a positional array instead of a keyed object.
        """
        from portfoy.data import AnalystView
        from portfoy.storage import Position

        monkeypatch.setattr(
            api_index.api_data.storage, "load_portfolio",
            lambda: [Position(symbol="AAPL", quantity=10.0, avg_cost=100.0,
                               currency="USD", added="2026-01-01", notes="")],
        )
        monkeypatch.setattr(
            api_index.api_data.data, "get_analyst_view",
            lambda sym: AnalystView(target_mean=200.0, target_high=None,
                                     target_low=None, consensus="al", num_analysts=5),
        )
        resp = client.get("/api/analyst", headers=AUTH)
        body = resp.get_json()
        assert isinstance(body["AAPL"], dict)
        assert body["AAPL"]["target_mean"] == 200.0
        assert body["AAPL"]["consensus"] == "al"

    def test_calendar_default_days(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "calendar_payload",
                             lambda days: captured.setdefault("d", days))
        client.get("/api/calendar", headers=AUTH)
        from portfoy import config
        assert captured["d"] == config.CALENDAR_LOOKAHEAD_DAYS

    def test_calendar_days_clamped_to_365(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "calendar_payload",
                             lambda days: captured.setdefault("d", days))
        client.get("/api/calendar?days=999999", headers=AUTH)
        assert captured["d"] == 365

    def test_calendar_days_clamped_to_1(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.api_data, "calendar_payload",
                             lambda days: captured.setdefault("d", days))
        client.get("/api/calendar?days=-5", headers=AUTH)
        assert captured["d"] == 1

    def test_news_normalizes_symbol_and_defaults_lang(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            api_index.api_data, "news_payload",
            lambda sym, lang: captured.update(sym=sym, lang=lang) or [],
        )
        client.get("/api/news/aapl", headers=AUTH)
        assert captured == {"sym": "AAPL", "lang": "tr"}

    def test_news_accepts_en_lang(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            api_index.api_data, "news_payload",
            lambda sym, lang: captured.update(sym=sym, lang=lang) or [],
        )
        client.get("/api/news/AAPL?lang=en", headers=AUTH)
        assert captured["lang"] == "en"

    def test_news_rejects_invalid_symbol(self, client):
        assert client.get("/api/news/%3Cbad%3E", headers=AUTH).status_code == 400

    def test_compare_defaults(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            api_index.api_data, "compare_payload",
            lambda period, base: captured.update(period=period, base=base) or [],
        )
        client.get("/api/compare", headers=AUTH)
        from portfoy import config
        assert captured == {"period": config.DEFAULT_COMPARE_PERIOD, "base": "USD"}

    def test_compare_rejects_unknown_period(self, client):
        resp = client.get("/api/compare?period=nope", headers=AUTH)
        assert resp.status_code == 400

    def test_compare_rejects_unknown_base(self, client):
        resp = client.get("/api/compare?base=EUR", headers=AUTH)
        assert resp.status_code == 400

    def test_compare_accepts_try_base(self, client, monkeypatch):
        monkeypatch.setattr(api_index.api_data, "compare_payload", lambda period, base: [])
        assert client.get("/api/compare?base=try", headers=AUTH).status_code == 200


class TestAddPosition:
    def test_persists_and_returns_updated_positions(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: True)
        monkeypatch.setattr(api_index.storage, "load_portfolio", lambda: [])
        monkeypatch.setattr(
            api_index.storage, "make_position",
            lambda symbol, qty, cost, notes="": {"symbol": symbol},
        )
        monkeypatch.setattr(
            api_index.storage, "upsert_position", lambda positions, new: [new],
        )
        monkeypatch.setattr(
            api_index.storage, "save_portfolio",
            lambda positions: captured.setdefault("saved", positions),
        )
        monkeypatch.setattr(
            api_index.api_data, "positions_payload",
            lambda: {"metrics": [], "cash": [], "usdtry": None},
        )
        resp = client.post(
            "/api/positions", headers=AUTH,
            json={"symbol": "AAPL", "quantity": 10, "avg_cost": 100.0},
        )
        assert resp.status_code == 200
        assert captured["saved"] == [{"symbol": "AAPL"}]

    def test_returns_503_when_storage_not_configured(self, client, monkeypatch):
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: False)
        resp = client.post("/api/positions", headers=AUTH, json={"symbol": "AAPL"})
        assert resp.status_code == 503
        assert resp.get_json() == {"error": "storage_not_configured"}

    def test_invalid_symbol_is_400(self, client, monkeypatch):
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: True)
        resp = client.post(
            "/api/positions", headers=AUTH,
            json={"symbol": "<bad>", "quantity": 1, "avg_cost": 1},
        )
        assert resp.status_code == 400

    def test_missing_body_is_400(self, client, monkeypatch):
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: True)
        resp = client.post("/api/positions", headers=AUTH)
        assert resp.status_code == 400


class TestDeletePosition:
    def test_removes_and_returns_updated_positions(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: True)
        monkeypatch.setattr(api_index.storage, "load_portfolio", lambda: ["x"])

        def fake_remove(positions, symbol):
            captured["removed"] = symbol
            return []

        monkeypatch.setattr(api_index.storage, "remove_position", fake_remove)
        monkeypatch.setattr(
            api_index.storage, "save_portfolio",
            lambda positions: captured.setdefault("saved", positions),
        )
        monkeypatch.setattr(
            api_index.api_data, "positions_payload",
            lambda: {"metrics": [], "cash": [], "usdtry": None},
        )
        resp = client.delete("/api/positions/aapl", headers=AUTH)
        assert resp.status_code == 200
        assert captured["removed"] == "AAPL"
        assert captured["saved"] == []

    def test_returns_503_when_storage_not_configured(self, client, monkeypatch):
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: False)
        resp = client.delete("/api/positions/AAPL", headers=AUTH)
        assert resp.status_code == 503

    def test_invalid_symbol_is_400(self, client, monkeypatch):
        monkeypatch.setattr(api_index.storage, "can_persist", lambda: True)
        resp = client.delete("/api/positions/%3Cbad%3E", headers=AUTH)
        assert resp.status_code == 400


class TestErrorShaping:
    def test_unhandled_exception_is_json_500(self, client, monkeypatch):
        def boom():
            raise RuntimeError("should never leak this message")

        monkeypatch.setattr(api_index.api_data, "macro_payload", boom)
        resp = client.get("/api/market/macro", headers=AUTH)
        assert resp.status_code == 500
        body = resp.get_json()
        assert body == {"error": "internal_error"}

    def test_unknown_route_is_json_404(self, client):
        resp = client.get("/api/does-not-exist", headers=AUTH)
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "not_found"}
