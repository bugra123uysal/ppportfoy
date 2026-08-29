"""Nemotron AI commentary -- a Turkish educational narration layer over
signals this codebase has *already computed*.

Every wrapper below is handed numbers other modules (report.py, money_flow.py,
rotation.py, rotation_overlap.py, vcp_scan.py, movers.py, breadth.py,
sentiment.py, yield_curve.py) produce mechanically. The model's job is to
explain those numbers -- what they mean together, why, and what general
lesson to take away -- never to invent a price, ratio, or ownership figure of
its own. See the project memory entry on the Hisse Raporu bundle (decision
#6) for the original scope call.

Uses NVIDIA's free NIM API (build.nvidia.com) over its OpenAI-compatible
chat-completions endpoint -- no SDK dependency, just `requests`. Two model
tiers, chosen for cost/latency vs. depth:

  NEMOTRON_SUPER_MODEL  -- most panels (scan-level, high call volume).
  NEMOTRON_ULTRA_MODEL  -- Hisse Raporu only (one call per click, so the
                           extra reasoning depth is worth the latency).

Requires an `NVIDIA_API_KEY` env var (free, no credit card -- generate one at
https://build.nvidia.com after signing in). NVIDIA's own supported-language
list for Nemotron 3 does not include Turkish, so real output quality should
be spot-checked after setup, not assumed.

Fails soft everywhere: no key, a network error, a timeout, rate-limiting, a
malformed response -- all of it returns ``None`` rather than raising. Every
feature this plugs into must keep working with the commentary field simply
absent, the same way `breadth_payload`/`sentiment_payload` already tolerate
missing market data.
"""

from __future__ import annotations

import json
import logging
import os

import requests

from . import config

_logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Sen bir Türkçe borsa eğitmenisin. Sana JSON olarak, bu sistemin zaten "
    "mekanik kurallarla hesapladığı göstergeler veriliyor -- SADECE bu "
    "sayılardan yorum üret, kendi fiyat/oran/yüzde UYDURMA ve JSON'da "
    "olmayan hiçbir veriye atıfta bulunma. Düz metin olarak, başlık ya da "
    "madde işareti kullanmadan, üç kısmı sırayla anlat:\n"
    "1) NE OLDU -- verilen sayıları 1-2 cümlede özetle.\n"
    "2) NEDEN -- göstergelerin birbiriyle ilişkisinden mekanik bir açıklama "
    "kur (örn. CMF pozitifken fiyat SMA50 üstündeyse birlikte ne anlama "
    "geldiğini anlat).\n"
    "3) DERS -- kullanıcının bu örnekten çıkarabileceği, başka hisselere de "
    "uygulayabileceği genel bir ders ver.\n"
    "Bu bir yatırım tavsiyesi değildir ve bir fiyat tahmini üretmiyorsun -- "
    "sadece zaten hesaplanmış olanı açıklıyor ve öğretiyorsun. Her bölüm "
    "birkaç cümle olsun, gereksiz uzatma."
)


def _ask(model: str, payload: dict, *, max_tokens: int = 500) -> str | None:
    """POST one chat-completion to NVIDIA's NIM endpoint. Never raises --
    any failure (missing key, network, HTTP, malformed body) is logged and
    swallowed into ``None`` so a commentary outage can never take an actual
    data endpoint down with it."""
    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        response = requests.post(
            f"{config.NEMOTRON_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.4,
                # Nemotron 3 defaults to "thinking" mode -- without this, its
                # chain-of-thought reasoning leaks straight into `content`
                # instead of a clean answer (confirmed against the live API:
                # "We need to respond in Turkish... So answer: 'Merhaba!'"
                # instead of just "Merhaba!"). We want the final Turkish
                # paragraph only, not the model's internal reasoning trace.
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=config.NEMOTRON_TIMEOUT,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip() or None
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as exc:
        _logger.warning("Nemotron commentary call failed (model=%s): %s", model, exc)
        return None


def symbol_report_commentary(report: object, context: object | None) -> str | None:
    """Hisse Raporu's flagship deep-dive -- the one commentary call that
    gets the strongest model (Ultra), since it's a single on-demand call per
    user click, not a per-row scan."""
    fib = getattr(report, "fib", None)
    payload = {
        "sembol": report.symbol,
        "fiyat": report.price,
        "gunluk_degisim_pct": report.change_1d,
        "trend": {
            "ema21_yukseliyor": report.ema21_rising,
            "ema50_yukseliyor": report.ema50_rising,
            "fiyat_vs_sma50": report.price_vs_sma50,
            "fiyat_vs_sma200": report.price_vs_sma200,
            "haftalik_trend_uyumlu": report.weekly_trend_aligned,
        },
        "momentum": {"rsi": report.rsi, "rsi_bolgesi": report.rsi_zone},
        "hacim": {
            "obv_trend": report.obv_trend,
            "cmf": report.cmf,
            "cmf_sinyal": report.cmf_signal,
            "mfi": report.mfi,
        },
        "hafta_52": {
            "zirveden_uzaklik_pct": report.pct_from_52w_high,
            "dipten_uzaklik_pct": report.pct_from_52w_low,
        },
        "fibonacci": (
            {
                "en_yakin_seviye": fib.nearest_ratio,
                "bolge": fib.zone_label,
                "seviyeye_yuzde_fark": fib.pct_to_nearest,
            }
            if fib is not None
            else None
        ),
        "opsiyon_put_call_orani": getattr(context, "put_call_ratio", None),
        "kurumsal_sahiplik_pct": getattr(context, "institutional_pct", None),
    }
    return _ask(config.NEMOTRON_ULTRA_MODEL, payload, max_tokens=700)


def money_flow_commentary(signals: list) -> str | None:
    """Para Akışı / opportunity-scan aggregate commentary -- top 5
    accumulation + top 5 distribution names, not the full universe (keeps
    the prompt small and the read focused on what actually stands out)."""
    accumulation = sorted(
        (s for s in signals if s.cmf_signal == "accumulation"),
        key=lambda s: s.cmf or 0.0,
        reverse=True,
    )[:5]
    distribution = sorted(
        (s for s in signals if s.cmf_signal == "distribution"),
        key=lambda s: s.cmf or 0.0,
    )[:5]
    if not accumulation and not distribution:
        return None
    payload = {
        "birikim_yapan_ust5": [
            {"sembol": s.symbol, "sektor": s.sector, "cmf": s.cmf, "mfi": s.mfi, "obv": s.obv_trend}
            for s in accumulation
        ],
        "dagitim_yapan_ust5": [
            {"sembol": s.symbol, "sektor": s.sector, "cmf": s.cmf, "mfi": s.mfi, "obv": s.obv_trend}
            for s in distribution
        ],
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def rotation_commentary(sectors: list) -> str | None:
    """Sector-rotation quadrant commentary -- teaches the RRG leading /
    improving / weakening / lagging cycle on top of the current snapshot."""
    if not sectors:
        return None
    payload = {
        "sektorler": [
            {
                "sektor": s.label_tr,
                "mevcut_kadran": s.quadrant,
                "onceki_kadran": s.prev_quadrant,
                "1a_getiri_pct": s.perf_1m,
                "3a_getiri_pct": s.perf_3m,
            }
            for s in sectors
        ]
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def rotation_overlap_commentary(candidates: list) -> str | None:
    if not candidates:
        return None
    payload = {
        "adaylar": [
            {
                "sembol": c.symbol,
                "sektor": c.sector,
                "1a_getiri_pct": c.perf_1m,
                "sinyaller": list(c.signals),
            }
            for c in candidates[:8]
        ]
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def vcp_commentary(candidates: list) -> str | None:
    if not candidates:
        return None
    payload = {
        "adaylar": [
            {
                "sembol": c.symbol,
                "sektor": c.sector,
                "3a_oncu_getiri_pct": c.trailing_return_pct,
                "range_daralma_pct": c.range_contraction_pct,
                "hacim_daralma_pct": c.volume_contraction_pct,
                "zirveden_uzaklik_pct": c.pct_from_52w_high,
            }
            for c in candidates[:8]
        ]
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def movers_commentary(gainers: list, volume_spikes: list) -> str | None:
    if not gainers and not volume_spikes:
        return None
    payload = {
        "gunun_yukselenleri": [
            {"sembol": m.symbol, "degisim_pct": m.change_pct, "goreli_hacim": m.relative_volume}
            for m in gainers[:5]
        ],
        "hacim_sivrileri": [
            {"sembol": m.symbol, "degisim_pct": m.change_pct, "goreli_hacim": m.relative_volume}
            for m in volume_spikes[:5]
        ],
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def trend_commentary(sectors: list, stocks: list) -> str | None:
    """Trend Bulucu -- en güçlü trendde sektörler + hisseler. Model, videonun
    3 katmanını (yapı/MA/trendline) zaten mekanik olarak hesaplanmış skorlar
    üzerinden anlatır, kendi trend/fiyat yorumu üretmez."""
    top_sectors = sectors[:5]
    top_stocks = stocks[:8]
    if not top_sectors and not top_stocks:
        return None
    payload = {
        "trendde_sektorler": [
            {"sektor": s.sector, "yon": s.direction, "guc": s.strength}
            for s in top_sectors
        ],
        "trendde_hisseler": [
            {
                "sembol": c.symbol,
                "sektor": c.sector,
                "yon": c.direction,
                "guc": c.strength,
                "ma_rejimi_teyit": c.ma_trend_confirmed,
                "trendline_teyit": c.trendline_confirmed,
                "hacim_teyit": c.volume_confirmed,
                "para_akisi": c.money_flow_signal,
                "para_akisi_uyumlu": c.money_flow_aligned,
                "adx": c.adx,
                "adx_yukseliyor": c.adx_rising,
                "trend_olgunlugu": c.trend_maturity,
                "rsi_diverjans_uyarisi": c.rsi_divergence_warning,
                "trend_yasi_gun": c.trend_age_days,
                "yeni_tetiklendi": c.newly_triggered,
            }
            for c in top_stocks
        ],
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)


def market_pulse_commentary(
    breadth: object | None,
    sentiment: object | None,
    yield_curve: object | None,
    macro: list[dict],
) -> str | None:
    """Piyasa Pusulası's headline digest -- synthesizes breadth, sentiment,
    yield-curve/credit-stress and macro tickers into one "is this a risk-on
    or risk-off market right now" read. The one commentary call that looks
    at the whole market instead of a single scan or symbol."""
    if breadth is None and sentiment is None and yield_curve is None and not macro:
        return None
    payload = {
        "genislik": (
            {
                "sma200_ustu_pct": breadth.pct_above_200,
                "yukselen_dusen": [breadth.advancers, breadth.decliners],
                "trin": breadth.trin,
                "mcclellan": breadth.mcclellan,
            }
            if breadth is not None
            else None
        ),
        "duygu_skoru": sentiment.composite if sentiment is not None else None,
        "getiri_egrisi": (
            {
                "spread_10y_3m": yield_curve.spread_10y_3m,
                "ters_egri": yield_curve.inverted,
                "kredi_stresi": yield_curve.credit_stress,
            }
            if yield_curve is not None
            else None
        ),
        "makro": [
            {"sembol": row["symbol"], "degisim_pct": row["change_pct"]} for row in macro
        ],
    }
    return _ask(config.NEMOTRON_SUPER_MODEL, payload)
