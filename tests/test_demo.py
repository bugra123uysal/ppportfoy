"""Demo mode: env flag parsing, disk fallback, and seed validity."""

from __future__ import annotations

import json

from portfoy import storage


def test_is_demo_accepts_truthy_values(monkeypatch):
    for value in ("1", "true", "YES", " True "):
        monkeypatch.setenv("PORTFOY_DEMO", value)
        assert storage.is_demo() is True


def test_is_demo_off_by_default(monkeypatch):
    monkeypatch.delenv("PORTFOY_DEMO", raising=False)
    assert storage.is_demo() is False
    monkeypatch.setenv("PORTFOY_DEMO", "0")
    assert storage.is_demo() is False


def test_session_store_is_none_outside_streamlit_runtime(monkeypatch):
    # Demo flag set, but no Streamlit server is running (e.g. pytest):
    # storage must fall back to plain disk files.
    monkeypatch.setenv("PORTFOY_DEMO", "1")
    assert storage._session_store() is None


def test_disk_storage_still_works_with_demo_flag_set(monkeypatch, tmp_path):
    monkeypatch.setenv("PORTFOY_DEMO", "1")
    path = tmp_path / "portfolio.json"
    position = storage.make_position("AAPL", 2, 100.0)
    storage.save_portfolio([position], path)
    loaded = storage.load_portfolio(path)
    assert [p.symbol for p in loaded] == ["AAPL"]


def test_demo_seed_positions_all_pass_validation(tmp_path):
    # Every seeded row must survive load_portfolio's validation untouched.
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps(storage.DEMO_SEED), encoding="utf-8")
    positions = storage.load_portfolio(path)
    cash = storage.load_cash(path)
    assert len(positions) == len(storage.DEMO_SEED["positions"])
    assert {c.currency for c in cash} == {"TRY", "USD"}
    bist = [p for p in positions if p.symbol.endswith(".IS")]
    assert all(p.currency == "TRY" for p in bist)
