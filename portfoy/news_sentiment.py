"""Deterministic, keyword-based sentiment tagging for news headlines.

Not NLP and not financial analysis -- a small bilingual (TR/EN) keyword list
scores each headline as positive/negative/neutral so the news feed gives an
at-a-glance read of tone. Pure and offline: no network calls, no added
latency, same input always yields the same output.
"""

from __future__ import annotations

POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"

# Case-insensitive substring matches against the headline. Keep entries
# lowercase; classify() lowercases the title before matching.
_POSITIVE_KEYWORDS = (
    # English
    "beats", "beat estimates", "tops estimates", "surge", "surges", "soar", "soars",
    "rally", "rallies", "upgrade", "upgraded", "record high", "strong demand",
    "buyback", "raises guidance", "outperform", "wins contract", "approval",
    "expands", "profit jumps", "earnings beat", "all-time high", "breakthrough",
    # Turkish
    "beklentileri aştı", "rekor kırdı", "rekor seviye", "yükseldi", "yükseliş",
    "sert yükseliş", "ralli", "artış", "kazanç artışı", "ortaklık", "onay aldı",
    "genişliyor", "kâr artışı", "kar artışı", "büyüme", "yükseltti", "güçlü talep",
    "geri alım", "hedef fiyatını yükseltti",
)
_NEGATIVE_KEYWORDS = (
    # English
    "misses", "miss estimates", "falls short", "plunge", "plunges", "slump", "slumps",
    "downgrade", "downgraded", "lawsuit", "investigation", "recall", "layoffs",
    "cuts guidance", "underperform", "fine", "probe", "warns", "loss widens",
    "sell-off", "selloff", "crash", "crashes", "bankruptcy", "delisted", "fraud",
    # Turkish
    "beklentilerin altında", "beklentileri karşılamadı", "düştü", "düşüş",
    "sert düşüş", "dava açıldı", "soruşturma", "geri çağırma", "işten çıkarma",
    "ceza kesildi", "uyardı", "zarar açıkladı", "satış baskısı", "çöküş",
    "düşürdü", "iflas", "hedef fiyatını düşürdü",
)

_INTERPRETATION = {
    POSITIVE: {
        "tr": "Başlıkta olumlu sinyaller var; kısa vadede fiyata destek verebilir.",
        "en": "This headline reads positive; it could support the price near-term.",
    },
    NEGATIVE: {
        "tr": "Başlıkta olumsuz sinyaller var; fiyat üzerinde baskı yaratabilir.",
        "en": "This headline reads negative; it could pressure the price near-term.",
    },
    NEUTRAL: {
        "tr": "Başlık nötr; belirgin bir fiyat etkisi öne çıkmıyor.",
        "en": "This headline reads neutral; no clear price impact stands out.",
    },
}

# Keyword matching alone is a heuristic, not a verdict -- every interpretation
# says so, so nobody mistakes a titlecheck for real analysis.
_DISCLAIMER = {
    "tr": " (anahtar kelime taraması, yatırım tavsiyesi değildir)",
    "en": " (keyword-based heuristic, not investment advice)",
}


def classify(title: str) -> str:
    """positive / negative / neutral, from keyword counts in the title."""
    lowered = title.lower()
    pos = sum(1 for kw in _POSITIVE_KEYWORDS if kw in lowered)
    neg = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in lowered)
    if pos > neg:
        return POSITIVE
    if neg > pos:
        return NEGATIVE
    return NEUTRAL


def interpret(title: str, lang: str = "tr") -> tuple[str, str]:
    """(sentiment, one-line interpretation) for a headline."""
    sentiment = classify(title)
    resolved_lang = lang if lang in ("tr", "en") else "tr"
    line = _INTERPRETATION[sentiment][resolved_lang] + _DISCLAIMER[resolved_lang]
    return sentiment, line
