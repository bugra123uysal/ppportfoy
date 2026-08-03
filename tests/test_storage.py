import json

import pytest

from portfoy import storage
from portfoy.security import ValidationError
from portfoy.storage import (
    append_snapshot,
    load_history,
    load_portfolio,
    make_position,
    reduce_position,
    remove_position,
    save_portfolio,
    upsert_position,
)


@pytest.fixture
def pos_aapl():
    return make_position("AAPL", 10, 150.0)


@pytest.fixture
def pos_thyao():
    return make_position("thyao.is", 100, 250.0, notes="uzun vade")


class TestMakePosition:
    def test_currency_detection(self, pos_aapl, pos_thyao):
        assert pos_aapl.currency == "USD"
        assert pos_thyao.currency == "TRY"

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValidationError):
            make_position("<bad>", 1, 1)


class TestRoundTrip:
    def test_save_and_load(self, tmp_path, pos_aapl, pos_thyao):
        path = tmp_path / "p.json"
        save_portfolio([pos_aapl, pos_thyao], path)
        loaded = load_portfolio(path)
        assert loaded == [pos_aapl, pos_thyao]

    def test_missing_file_is_empty(self, tmp_path):
        assert load_portfolio(tmp_path / "nope.json") == []

    def test_corrupt_file_is_empty(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        assert load_portfolio(path) == []

    def test_invalid_entries_skipped(self, tmp_path, pos_aapl):
        path = tmp_path / "p.json"
        payload = [
            {"symbol": "AAPL", "quantity": 10, "avg_cost": 150.0,
             "currency": "USD", "added": "2026-01-01", "notes": ""},
            {"symbol": "<script>", "quantity": 1, "avg_cost": 1},
            {"symbol": "MSFT", "quantity": -5, "avg_cost": 100},
            "garbage",
        ]
        path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_portfolio(path)
        assert [p.symbol for p in loaded] == ["AAPL"]


class TestMutations:
    def test_upsert_new_keeps_original_untouched(self, pos_aapl, pos_thyao):
        original = [pos_aapl]
        result = upsert_position(original, pos_thyao)
        assert len(original) == 1 and len(result) == 2

    def test_upsert_merges_avg_cost(self, pos_aapl):
        more = make_position("AAPL", 10, 170.0)
        merged = upsert_position([pos_aapl], more)[0]
        assert merged.quantity == 20
        assert merged.avg_cost == pytest.approx(160.0)

    def test_remove(self, pos_aapl, pos_thyao):
        assert remove_position([pos_aapl, pos_thyao], "AAPL") == [pos_thyao]

    def test_reduce_partial(self, pos_aapl):
        result = reduce_position([pos_aapl], "AAPL", 4)
        assert result[0].quantity == pytest.approx(6)

    def test_reduce_to_zero_removes(self, pos_aapl):
        assert reduce_position([pos_aapl], "AAPL", 10) == []


class TestEnvFallback:
    """data/ is gitignored, so a git-based deploy (Vercel) never has the
    file -- PORTFOY_PORTFOLIO_JSON / PORTFOY_HISTORY_JSON substitute."""

    def test_missing_file_falls_back_to_env_json(self, tmp_path, monkeypatch):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._ENV_FALLBACKS, target, "PORTFOY_TEST_JSON")
        monkeypatch.setenv("PORTFOY_TEST_JSON", json.dumps({
            "positions": [{"symbol": "AAPL", "quantity": 10, "avg_cost": 150.0,
                           "currency": "USD", "added": "2026-01-01", "notes": ""}],
            "cash": [],
        }))
        assert [p.symbol for p in load_portfolio(target)] == ["AAPL"]

    def test_missing_file_without_env_var_stays_empty(self, tmp_path):
        assert load_portfolio(tmp_path / "nope2.json") == []

    def test_invalid_env_json_falls_back_to_empty(self, tmp_path, monkeypatch):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._ENV_FALLBACKS, target, "PORTFOY_TEST_JSON")
        monkeypatch.setenv("PORTFOY_TEST_JSON", "{not json")
        assert load_portfolio(target) == []

    def test_existing_file_takes_priority_over_env(self, tmp_path, monkeypatch, pos_aapl):
        target = tmp_path / "portfolio.json"
        save_portfolio([pos_aapl], target)
        monkeypatch.setitem(storage._ENV_FALLBACKS, target, "PORTFOY_TEST_JSON")
        monkeypatch.setenv("PORTFOY_TEST_JSON", json.dumps({"positions": [], "cash": []}))
        assert [p.symbol for p in load_portfolio(target)] == ["AAPL"]


class TestHistory:
    def test_snapshot_one_per_day(self, tmp_path):
        path = tmp_path / "h.json"
        append_snapshot(100.0, 3.0, path)
        history = append_snapshot(200.0, 6.0, path)
        assert len(history) == 1
        assert history[0]["value_try"] == 200.0
        assert load_history(path) == history


class FakePersistentBackend:
    """In-memory stand-in for cache.UpstashBackend, so storage's persistent
    path can be tested without a real Upstash project."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def set_forever(self, key, value):
        self.store[key] = value


class TestPersistentStorage:
    """When Upstash is configured, reads/writes to the portfolio/history
    file paths go through it instead of local disk -- this is what makes
    add/remove-position durable on Vercel's read-only filesystem.

    Uses a tmp_path target registered into storage._PERSISTENT_KEYS (same
    pattern TestEnvFallback uses for _ENV_FALLBACKS) rather than the real
    config.PORTFOLIO_FILE, since a real data/portfolio.json exists on disk
    in local dev and would otherwise leak into these assertions.
    """

    def test_write_then_read_round_trips_through_backend(self, tmp_path, monkeypatch, pos_aapl):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._PERSISTENT_KEYS, target, "test:persistent:key")
        backend = FakePersistentBackend()
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: backend)
        save_portfolio([pos_aapl], target)
        assert load_portfolio(target) == [pos_aapl]
        assert backend.store  # something was actually written

    def test_persistent_value_wins_over_env_fallback(self, tmp_path, monkeypatch, pos_aapl):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._PERSISTENT_KEYS, target, "test:persistent:key")
        monkeypatch.setitem(storage._ENV_FALLBACKS, target, "PORTFOY_TEST_JSON")
        backend = FakePersistentBackend()
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: backend)
        monkeypatch.setenv("PORTFOY_TEST_JSON", json.dumps({"positions": [], "cash": []}))
        save_portfolio([pos_aapl], target)
        assert [p.symbol for p in load_portfolio(target)] == ["AAPL"]

    def test_falls_back_to_env_seed_before_first_write(self, tmp_path, monkeypatch):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._PERSISTENT_KEYS, target, "test:persistent:key")
        monkeypatch.setitem(storage._ENV_FALLBACKS, target, "PORTFOY_TEST_JSON")
        backend = FakePersistentBackend()
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: backend)
        monkeypatch.setenv(
            "PORTFOY_TEST_JSON",
            json.dumps({
                "positions": [{"symbol": "AAPL", "quantity": 10, "avg_cost": 150.0,
                               "currency": "USD", "added": "2026-01-01", "notes": ""}],
                "cash": [],
            }),
        )
        assert [p.symbol for p in load_portfolio(target)] == ["AAPL"]

    def test_backend_read_failure_falls_back_gracefully(self, tmp_path, monkeypatch):
        target = tmp_path / "portfolio.json"
        monkeypatch.setitem(storage._PERSISTENT_KEYS, target, "test:persistent:key")

        class BrokenBackend:
            def get(self, key):
                raise ConnectionError("unreachable")

        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: BrokenBackend())
        assert load_portfolio(target) == []


class TestCanPersist:
    def test_true_when_upstash_configured(self, monkeypatch):
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: object())
        assert storage.can_persist() is True

    def test_true_locally_without_upstash(self, monkeypatch):
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: None)
        monkeypatch.delenv("VERCEL", raising=False)
        assert storage.can_persist() is True

    def test_false_on_vercel_without_upstash(self, monkeypatch):
        monkeypatch.setattr(storage.cache, "get_persistent_backend", lambda: None)
        monkeypatch.setenv("VERCEL", "1")
        assert storage.can_persist() is False
