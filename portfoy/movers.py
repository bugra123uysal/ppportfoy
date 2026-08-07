"""Günün ABD hisse hareketlileri: "day gainers" + hacim öncüllüğü taraması.

İki tamamlayıcı, ücretsiz sinyal (bkz. config.py'deki MOVERS_* eşikleri):

  1. Day gainers: Yahoo'nun kendi günlük sıralaması (``yf.screen("day_gainers")``)
     -- zaten büyük ölçüde hareket etmiş isimler, geriye dönük ama sıfır
     maliyetli.
  2. Hacim öncüllüğü: fiyat henüz büyük hareket etmemişken (dar bir % aralıkta)
     hacmi 3 aylık ortalamasının kat kat üstüne çıkmış isimler -- "hacim
     genelde fiyattan önce gelir" mantığıyla olası erken adaylar. Yahoo'nun
     screen() API'si bir "relative volume" alanı sunmadığı için geniş bir
     aday havuzu çekilip oran istemci tarafında hesaplanır ve filtrelenir.

Her iki listedeki isimler ayrıca ``trade_scan``'in Group 1-4 teknik
kurulumlarına karşı taranır (aynı OHLCV fetch'i tekrar kullanarak, ikinci bir
ağ isteği olmadan) ve en çok öne çıkan isimler için ``news`` modülünden son
haber başlıkları eklenir -- "neden yükseliyor" sorusuna hızlı bir cevap.

Sadece ABD piyasası: Yahoo'nun screen() API'si BIST için güvenilir/kapsamlı
bir evren sunmuyor.

Sonuç periyodik olarak (bkz. api/index.py'nin /api/movers/scan'i, dış bir
zamanlayıcı tarafından tetiklenir) hesaplanıp Upstash'e yazılır -- sayfa
ziyaretinde yeniden hesaplanmaz, en son anlık görüntü okunur. Bu bir al/sat
sinyali değildir, yatırım tavsiyesi değildir.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime

import yfinance as yf
from yfinance import EquityQuery

from . import cache, config, data, news
from .cache import cached
from .serialize import dumps
from .trade_scan import TradeSignal, scan_symbol

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Mover:
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: int | None
    avg_volume_3m: int | None
    relative_volume: float | None  # volume / avg_volume_3m; None if either is missing
    sector: str | None
    signals: list[TradeSignal]  # trade_scan Group 1-4 cross-check, may be empty
    news: list[dict]  # recent headlines, may be empty (only top-N get this)


@dataclass(frozen=True)
class MoversScan:
    generated_at: str  # ISO timestamp of this scan
    gainers: list[Mover]
    volume_spikes: list[Mover]


def _safe_number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _parse_quote(q: dict) -> dict | None:
    """Raw Yahoo screen() quote -> a plain dict, or None if fields we need are missing."""
    symbol = q.get("symbol")
    price = _safe_number(q.get("regularMarketPrice"))
    change_pct = _safe_number(q.get("regularMarketChangePercent"))
    if not symbol or price is None or change_pct is None:
        return None
    volume = _safe_number(q.get("regularMarketVolume"))
    avg_volume = _safe_number(q.get("averageDailyVolume3Month"))
    return {
        "symbol": str(symbol),
        "name": q.get("shortName") or q.get("longName") or str(symbol),
        "price": price,
        "change_pct": change_pct,
        "volume": int(volume) if volume is not None else None,
        "avg_volume_3m": int(avg_volume) if avg_volume is not None else None,
        "sector": q.get("sector"),
    }


def _relative_volume(volume: int | None, avg_volume: int | None) -> float | None:
    if not volume or not avg_volume:
        return None
    return volume / avg_volume


@cached(ttl=config.MOVERS_FETCH_CACHE_TTL)
def _fetch_day_gainers(count: int = config.MOVERS_GAINERS_COUNT) -> list[dict]:
    try:
        result = yf.screen("day_gainers", count=count)
    except Exception:
        _logger.warning("movers: day_gainers screen() failed", exc_info=True)
        return []
    quotes = (result or {}).get("quotes", [])
    return [parsed for q in quotes if (parsed := _parse_quote(q)) is not None]


@cached(ttl=config.MOVERS_FETCH_CACHE_TTL)
def _fetch_volume_spikes(
    pool_size: int = config.MOVERS_SPIKE_CANDIDATE_POOL,
    top_n: int = config.MOVERS_SPIKE_TOP_N,
) -> list[dict]:
    query = EquityQuery(
        "and",
        [
            EquityQuery(
                "btwn",
                ["percentchange", -config.MOVERS_SPIKE_FLAT_PCT, config.MOVERS_SPIKE_FLAT_PCT],
            ),
            EquityQuery("eq", ["region", "us"]),
            EquityQuery("gte", ["intradaymarketcap", config.MOVERS_SPIKE_MIN_MARKETCAP]),
        ],
    )
    try:
        result = yf.screen(query, sortField="dayvolume", sortAsc=False, size=pool_size)
    except Exception:
        _logger.warning("movers: volume-spike screen() failed", exc_info=True)
        return []
    quotes = (result or {}).get("quotes", [])
    candidates = [parsed for q in quotes if (parsed := _parse_quote(q)) is not None]
    spikes = [
        c
        for c in candidates
        if (rvol := _relative_volume(c["volume"], c["avg_volume_3m"])) is not None
        and rvol >= config.MOVERS_SPIKE_RVOL_THRESHOLD
    ]
    spikes.sort(
        key=lambda c: _relative_volume(c["volume"], c["avg_volume_3m"]) or 0.0, reverse=True
    )
    return spikes[:top_n]


def _attach_news(gainers_raw: list[dict], spikes_raw: list[dict]) -> dict[str, list[dict]]:
    """Fetches news for the top names concurrently -- each get_news_for() call
    is 1-2 sequential outbound HTTP requests (Yahoo + Google News RSS, see
    news.py), so doing this one symbol at a time for up to
    2*MOVERS_NEWS_TOP_N names risked blowing past the scan's own time budget
    (the GitHub Actions trigger times out at 60s, see movers-scan.yml)."""
    top_symbols = list(
        dict.fromkeys(
            [r["symbol"] for r in gainers_raw[: config.MOVERS_NEWS_TOP_N]]
            + [r["symbol"] for r in spikes_raw[: config.MOVERS_NEWS_TOP_N]]
        )
    )
    if not top_symbols:
        return {}
    workers = min(len(top_symbols), config.MOVERS_NEWS_MAX_WORKERS)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda sym: news.get_news_for(sym, "tr"), top_symbols)
        return dict(zip(top_symbols, results, strict=True))


def _raw_to_mover(raw: dict, signals: list[TradeSignal], news_items: list[dict]) -> Mover:
    return Mover(
        symbol=raw["symbol"],
        name=raw["name"],
        price=raw["price"],
        change_pct=raw["change_pct"],
        volume=raw["volume"],
        avg_volume_3m=raw["avg_volume_3m"],
        relative_volume=_relative_volume(raw["volume"], raw["avg_volume_3m"]),
        sector=raw["sector"],
        signals=signals,
        news=news_items,
    )


def build_movers_scan() -> MoversScan:
    """Fetch gainers + volume spikes, cross-check both against trade_scan's
    technical setups, attach news for the most notable names, and package
    the result. This is the expensive path -- meant to run periodically from
    a scheduled trigger (see api/index.py), not on every page load."""
    gainers_raw = _fetch_day_gainers()
    spikes_raw = _fetch_volume_spikes()

    universe = list(dict.fromkeys([r["symbol"] for r in (*gainers_raw, *spikes_raw)]))
    histories = (
        data.get_histories(tuple(universe), period=config.TRADE_SCAN_HISTORY_PERIOD)
        if universe
        else {}
    )
    signals_by_symbol = {
        sym: scan_symbol(sym, "", histories[sym])
        for sym in universe
        if sym in histories and not histories[sym].empty
    }
    news_by_symbol = _attach_news(gainers_raw, spikes_raw)

    def to_mover(raw: dict) -> Mover:
        return _raw_to_mover(
            raw, signals_by_symbol.get(raw["symbol"], []), news_by_symbol.get(raw["symbol"], [])
        )

    return MoversScan(
        generated_at=datetime.now(UTC).isoformat(),
        gainers=[to_mover(r) for r in gainers_raw],
        volume_spikes=[to_mover(r) for r in spikes_raw],
    )


def save_snapshot(scan: MoversScan) -> None:
    """Persist the latest scan so the read endpoint never recomputes it --
    best-effort, same as every other cache write in this codebase (see
    cache.py's module docstring): a failed write just means the next read
    falls back to build_movers_scan() itself."""
    backend = cache.get_persistent_backend()
    if backend is None:
        return
    try:
        backend.set_forever(config.MOVERS_SNAPSHOT_KEY, dumps(scan))
    except Exception:  # noqa: S110 -- best-effort, see docstring above
        pass


def load_snapshot() -> dict | None:
    """The last persisted scan as a plain (already-JSON-safe) dict, or None
    when nothing has been persisted yet (no Upstash configured, first ever
    run before any scan trigger has fired, or a transient read failure)."""
    backend = cache.get_persistent_backend()
    if backend is None:
        return None
    try:
        raw = backend.get(config.MOVERS_SNAPSHOT_KEY)
    except Exception:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def scan_if_due(
    min_interval_seconds: int = config.MOVERS_MIN_SCAN_INTERVAL_SECONDS,
) -> dict | MoversScan:
    """Re-scans and persists only if the last snapshot is missing or older
    than min_interval_seconds -- a cost backstop independent of the
    CRON_SECRET/PORTFOY_API_KEY gates in front of this (see api/index.py and
    web/src/app/api/cron/movers-scan/route.ts): if either secret is ever
    compromised, this bounds how often the expensive live scan can actually
    run, regardless of how often the endpoint itself gets hit."""
    snapshot = load_snapshot()
    if snapshot is not None:
        try:
            generated_at = datetime.fromisoformat(snapshot["generated_at"])
            age = (datetime.now(UTC) - generated_at).total_seconds()
        except (KeyError, TypeError, ValueError):
            age = None  # corrupt/missing timestamp -- fall through and rescan
        if age is not None and age < min_interval_seconds:
            return snapshot

    scan = build_movers_scan()
    save_snapshot(scan)
    return scan
