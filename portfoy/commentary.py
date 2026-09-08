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


def stage_commentary(stages: list) -> str | None:
    """Evre Takibi -- portföydeki her pozisyonun Weinstein 4 evre okuması.
    Model, evre geçişlerinin ve teknik bozukluk uyarılarının ne anlama
    geldiğini zaten mekanik olarak hesaplanmış alanlar üzerinden anlatır."""
    if not stages:
        return None
    payload = {
        "pozisyonlar": [
            {
                "sembol": s.symbol,
                "evre": s.stage,
                "trend": s.trend,
                "evre_bu_hafta_degisti": s.stage_changed,
                "sma30h_egim_pct": s.sma30w_slope_pct,
                "fiyat_vs_sma_pct": s.price_vs_sma_pct,
                "bu_evrede_hafta": s.weeks_in_stage,
                "goreli_guc_trendi": s.relative_strength_trend,
                "teknik_bozukluk": s.technical_alert,
            }
            for s in stages
        ]
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
