import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from portfoy import config, movers
from portfoy.cache import InProcessBackend, set_backend
from portfoy.movers import (
    Mover,
    MoversScan,
    _attach_news,
    _fetch_day_gainers,
    _fetch_volume_spikes,
    _parse_quote,
    _relative_volume,
    build_movers_scan,
    load_snapshot,
    save_snapshot,
    scan_if_due,
)
from portfoy.trade_scan import TradeSignal

N = 40


@pytest.fixture(autouse=True)
def isolated_cache():
    """_fetch_day_gainers/_fetch_volume_spikes are @cached -- give every test
    a fresh backend so results from one test don't leak into the next via
    the shared process cache (see tests/test_news.py for the same pattern)."""
    set_backend(InProcessBackend())
    yield
    set_backend(None)


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


def _quote(**overrides) -> dict:
    base = {
        "symbol": "AAA",
        "shortName": "AAA Inc.",
        "regularMarketPrice": 10.0,
        "regularMarketChangePercent": 5.0,
        "regularMarketVolume": 2_000_000,
        "averageDailyVolume3Month": 1_000_000,
        "sector": "Technology",
    }
    base.update(overrides)
    return base


class FakePersistentBackend:
    """In-memory stand-in for cache.UpstashBackend (see tests/test_storage.py)."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def set_forever(self, key, value):
        self.store[key] = value


class TestParseQuote:
    def test_parses_full_quote(self):
        parsed = _parse_quote(_quote())
        assert parsed == {
            "symbol": "AAA",
            "name": "AAA Inc.",
            "price": 10.0,
            "change_pct": 5.0,
            "volume": 2_000_000,
            "avg_volume_3m": 1_000_000,
            "sector": "Technology",
        }

    def test_falls_back_to_long_name(self):
        parsed = _parse_quote(_quote(shortName=None, longName="AAA Corp"))
        assert parsed["name"] == "AAA Corp"

    def test_falls_back_to_symbol_when_no_name(self):
        parsed = _parse_quote(_quote(shortName=None))
        assert parsed["name"] == "AAA"

    def test_none_without_symbol(self):
        assert _parse_quote(_quote(symbol=None)) is None

    def test_none_without_price(self):
        assert _parse_quote(_quote(regularMarketPrice=None)) is None

    def test_none_without_change_pct(self):
        assert _parse_quote(_quote(regularMarketChangePercent=None)) is None

    def test_missing_volume_fields_become_none_not_rejected(self):
        parsed = _parse_quote(_quote(regularMarketVolume=None, averageDailyVolume3Month=None))
        assert parsed is not None
        assert parsed["volume"] is None
        assert parsed["avg_volume_3m"] is None

    def test_missing_sector_becomes_none(self):
        parsed = _parse_quote(_quote(sector=None))
        assert parsed["sector"] is None


class TestRelativeVolume:
    def test_normal_ratio(self):
        assert _relative_volume(2_000_000, 1_000_000) == pytest.approx(2.0)

    def test_none_when_volume_missing(self):
        assert _relative_volume(None, 1_000_000) is None

    def test_none_when_avg_missing(self):
        assert _relative_volume(1_000_000, None) is None

    def test_none_when_avg_is_zero(self):
        assert _relative_volume(1_000_000, 0) is None


class TestFetchDayGainers:
    def test_parses_quotes_from_screen(self, monkeypatch):
        monkeypatch.setattr(
            movers.yf,
            "screen",
            lambda query, count=None: {"quotes": [_quote(), _quote(symbol="BBB")]},
        )
        out = _fetch_day_gainers()
        assert [r["symbol"] for r in out] == ["AAA", "BBB"]

    def test_drops_unparseable_quotes(self, monkeypatch):
        monkeypatch.setattr(
            movers.yf,
            "screen",
            lambda query, count=None: {"quotes": [_quote(), _quote(symbol=None)]},
        )
        out = _fetch_day_gainers()
        assert len(out) == 1

    def test_empty_on_exception(self, monkeypatch):
        def boom(*args, **kwargs):
            raise ConnectionError("yahoo unreachable")

        monkeypatch.setattr(movers.yf, "screen", boom)
        assert _fetch_day_gainers() == []

    def test_empty_when_screen_returns_none(self, monkeypatch):
        monkeypatch.setattr(movers.yf, "screen", lambda query, count=None: None)
        assert _fetch_day_gainers() == []


class TestFetchVolumeSpikes:
    def test_filters_below_rvol_threshold(self, monkeypatch):
        # 1.2x -- below the default 2.0x threshold, must be excluded.
        low_rvol = _quote(
            symbol="LOW", regularMarketVolume=1_200_000, averageDailyVolume3Month=1_000_000
        )
        # 3x -- above threshold, must be included.
        high_rvol = _quote(
            symbol="HIGH", regularMarketVolume=3_000_000, averageDailyVolume3Month=1_000_000
        )
        monkeypatch.setattr(
            movers.yf,
            "screen",
            lambda query, sortField=None, sortAsc=None, size=None: {
                "quotes": [low_rvol, high_rvol]
            },
        )
        out = _fetch_volume_spikes()
        assert [r["symbol"] for r in out] == ["HIGH"]

    def test_sorted_by_rvol_descending(self, monkeypatch):
        mid = _quote(
            symbol="MID", regularMarketVolume=2_500_000, averageDailyVolume3Month=1_000_000
        )
        top = _quote(
            symbol="TOP", regularMarketVolume=5_000_000, averageDailyVolume3Month=1_000_000
        )
        monkeypatch.setattr(
            movers.yf,
            "screen",
            lambda query, sortField=None, sortAsc=None, size=None: {"quotes": [mid, top]},
        )
        out = _fetch_volume_spikes()
        assert [r["symbol"] for r in out] == ["TOP", "MID"]

    def test_respects_top_n(self, monkeypatch):
        quotes = [
            _quote(
                symbol=f"S{i}", regularMarketVolume=3_000_000, averageDailyVolume3Month=1_000_000
            )
            for i in range(5)
        ]
        monkeypatch.setattr(
            movers.yf,
            "screen",
            lambda query, sortField=None, sortAsc=None, size=None: {"quotes": quotes},
        )
        out = _fetch_volume_spikes(top_n=2)
        assert len(out) == 2

    def test_empty_on_exception(self, monkeypatch):
        def boom(*args, **kwargs):
            raise ConnectionError("yahoo unreachable")

        monkeypatch.setattr(movers.yf, "screen", boom)
        assert _fetch_volume_spikes() == []


class TestAttachNews:
    def test_attaches_news_per_symbol_up_to_top_n(self, monkeypatch):
        monkeypatch.setattr(config, "MOVERS_NEWS_TOP_N", 1)
        calls = []

        def fake_news(symbol, lang):
            calls.append(symbol)
            return [{"title": f"{symbol} news"}]

        monkeypatch.setattr(movers.news, "get_news_for", fake_news)
        gainers = [_parse_quote(_quote(symbol="AAA")), _parse_quote(_quote(symbol="BBB"))]
        spikes = [_parse_quote(_quote(symbol="CCC"))]

        result = _attach_news(gainers, spikes)

        # Only the first MOVERS_NEWS_TOP_N (=1) name from each list gets news.
        assert set(calls) == {"AAA", "CCC"}
        assert result["AAA"] == [{"title": "AAA news"}]
        assert "BBB" not in result

    def test_dedupes_symbol_appearing_in_both_lists(self, monkeypatch):
        calls = []

        def fake_news(symbol, lang):
            calls.append(symbol)
            return []

        monkeypatch.setattr(movers.news, "get_news_for", fake_news)
        gainers = [_parse_quote(_quote(symbol="AAA"))]
        spikes = [_parse_quote(_quote(symbol="AAA"))]

        _attach_news(gainers, spikes)

        assert calls == ["AAA"]


class TestBuildMoversScan:
    def _stub_signal(self, symbol: str) -> TradeSignal:
        return TradeSignal(
            symbol=symbol,
            sector="",
            price=10.0,
            change_1d=1.0,
            direction="long",
            groups=[1],
            atr_14=None,
            suggested_stop=None,
            pct_from_52w_high=None,
            pct_from_52w_low=None,
            weekly_trend_aligned=None,
        )

    def test_assembles_movers_with_signals_and_news(self, monkeypatch):
        monkeypatch.setattr(
            movers, "_fetch_day_gainers", lambda: [_parse_quote(_quote(symbol="AAA"))]
        )
        monkeypatch.setattr(
            movers, "_fetch_volume_spikes", lambda: [_parse_quote(_quote(symbol="BBB"))]
        )
        histories = {"AAA": _frame([100.0] * N), "BBB": _frame([50.0] * N)}
        monkeypatch.setattr(movers.data, "get_histories", lambda symbols, period=None: histories)
        monkeypatch.setattr(movers, "scan_symbol", lambda sym, sector, df: [self._stub_signal(sym)])
        monkeypatch.setattr(
            movers.news, "get_news_for", lambda sym, lang: [{"title": f"{sym} news"}]
        )

        scan = build_movers_scan()

        assert isinstance(scan, MoversScan)
        assert scan.generated_at  # non-empty ISO timestamp
        assert len(scan.gainers) == 1
        assert isinstance(scan.gainers[0], Mover)
        assert scan.gainers[0].symbol == "AAA"
        assert scan.gainers[0].signals == [self._stub_signal("AAA")]
        assert scan.gainers[0].news == [{"title": "AAA news"}]
        assert scan.volume_spikes[0].symbol == "BBB"

    def test_symbol_missing_from_histories_gets_no_signals(self, monkeypatch):
        monkeypatch.setattr(
            movers, "_fetch_day_gainers", lambda: [_parse_quote(_quote(symbol="AAA"))]
        )
        monkeypatch.setattr(movers, "_fetch_volume_spikes", lambda: [])
        monkeypatch.setattr(movers.data, "get_histories", lambda symbols, period=None: {})
        monkeypatch.setattr(movers.news, "get_news_for", lambda sym, lang: [])

        scan = build_movers_scan()

        assert scan.gainers[0].signals == []

    def test_empty_gainers_and_spikes_produce_empty_scan(self, monkeypatch):
        monkeypatch.setattr(movers, "_fetch_day_gainers", lambda: [])
        monkeypatch.setattr(movers, "_fetch_volume_spikes", lambda: [])
        monkeypatch.setattr(movers.data, "get_histories", lambda symbols, period=None: {})

        scan = build_movers_scan()

        assert scan.gainers == []
        assert scan.volume_spikes == []


class TestSnapshotPersistence:
    def test_save_is_noop_without_backend(self, monkeypatch):
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: None)
        scan = MoversScan(generated_at="2026-01-01T00:00:00+00:00", gainers=[], volume_spikes=[])
        save_snapshot(scan)  # must not raise

    def test_load_is_none_without_backend(self, monkeypatch):
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: None)
        assert load_snapshot() is None

    def test_save_then_load_round_trips(self, monkeypatch):
        backend = FakePersistentBackend()
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: backend)
        mover = Mover(
            symbol="AAA",
            name="AAA Inc.",
            price=10.0,
            change_pct=5.0,
            volume=2_000_000,
            avg_volume_3m=1_000_000,
            relative_volume=2.0,
            sector="Technology",
            signals=[
                TradeSignal(
                    symbol="AAA",
                    sector="",
                    price=10.0,
                    change_1d=1.0,
                    direction="long",
                    groups=[1],
                    atr_14=None,
                    suggested_stop=None,
                    pct_from_52w_high=None,
                    pct_from_52w_low=None,
                    weekly_trend_aligned=None,
                )
            ],
            news=[{"title": "AAA news"}],
        )
        scan = MoversScan(
            generated_at="2026-01-01T00:00:00+00:00", gainers=[mover], volume_spikes=[]
        )

        save_snapshot(scan)
        loaded = load_snapshot()

        assert backend.store  # something was written
        assert loaded["generated_at"] == "2026-01-01T00:00:00+00:00"
        assert loaded["gainers"][0]["symbol"] == "AAA"
        assert loaded["gainers"][0]["relative_volume"] == pytest.approx(2.0)
        assert loaded["gainers"][0]["signals"][0]["groups"] == [1]
        assert loaded["gainers"][0]["news"] == [{"title": "AAA news"}]
        assert loaded["volume_spikes"] == []

    def test_load_returns_none_on_corrupt_json(self, monkeypatch):
        backend = FakePersistentBackend()
        backend.store[config.MOVERS_SNAPSHOT_KEY] = "not json"
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: backend)
        assert load_snapshot() is None

    def test_load_returns_none_on_backend_read_failure(self, monkeypatch):
        class BrokenBackend:
            def get(self, key):
                raise ConnectionError("unreachable")

        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: BrokenBackend())
        assert load_snapshot() is None


class TestScanIfDue:
    def _fresh_scan(self) -> MoversScan:
        return MoversScan(generated_at=datetime.now(UTC).isoformat(), gainers=[], volume_spikes=[])

    def test_returns_existing_snapshot_without_rescanning_when_fresh(self, monkeypatch):
        backend = FakePersistentBackend()
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: backend)
        recent = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
        save_snapshot(MoversScan(generated_at=recent, gainers=[], volume_spikes=[]))

        called = []
        monkeypatch.setattr(movers, "build_movers_scan", lambda: called.append(1))

        result = scan_if_due(min_interval_seconds=300)

        assert called == []
        assert result["generated_at"] == recent

    def test_rescans_and_persists_when_snapshot_is_stale(self, monkeypatch):
        backend = FakePersistentBackend()
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: backend)
        stale = (datetime.now(UTC) - timedelta(seconds=600)).isoformat()
        save_snapshot(MoversScan(generated_at=stale, gainers=[], volume_spikes=[]))
        fresh_scan = self._fresh_scan()
        monkeypatch.setattr(movers, "build_movers_scan", lambda: fresh_scan)

        result = scan_if_due(min_interval_seconds=300)

        assert result is fresh_scan
        persisted = json.loads(backend.store[config.MOVERS_SNAPSHOT_KEY])
        assert persisted["generated_at"] == fresh_scan.generated_at

    def test_rescans_when_no_snapshot_exists(self, monkeypatch):
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: FakePersistentBackend())
        fresh_scan = self._fresh_scan()
        monkeypatch.setattr(movers, "build_movers_scan", lambda: fresh_scan)

        assert scan_if_due() is fresh_scan

    def test_rescans_when_generated_at_is_corrupt(self, monkeypatch):
        backend = FakePersistentBackend()
        backend.store[config.MOVERS_SNAPSHOT_KEY] = json.dumps(
            {"generated_at": "not-a-date", "gainers": [], "volume_spikes": []}
        )
        monkeypatch.setattr(movers.cache, "get_persistent_backend", lambda: backend)
        fresh_scan = self._fresh_scan()
        monkeypatch.setattr(movers, "build_movers_scan", lambda: fresh_scan)

        assert scan_if_due() is fresh_scan
