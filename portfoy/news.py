"""Free news sources for the holdings: Yahoo Finance + Google News RSS.

No API keys. RSS XML is parsed with defusedxml to stay safe against
malicious XML (entity expansion attacks), and every link is checked
with is_safe_url before it reaches the UI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import requests
import streamlit as st
import yfinance as yf
from defusedxml import ElementTree as SafeET

from . import config
from .security import is_safe_url


@st.cache_data(ttl=config.NEWS_CACHE_TTL, show_spinner=False)
def get_news_for(symbol: str, lang: str = "tr") -> list[dict]:
    """Merged, deduplicated, newest-first news list for one symbol."""
    items = _yahoo_news(symbol) + _google_news(symbol, lang)
    seen: set[str] = set()
    unique = []
    for item in items:
        key = item["title"].strip().lower()[:120]
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    unique.sort(key=lambda x: x["published"], reverse=True)
    return unique[: config.NEWS_PER_SYMBOL]


def _yahoo_news(symbol: str) -> list[dict]:
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        return []
    items = []
    for entry in raw[: config.NEWS_PER_SYMBOL]:
        content = entry.get("content", entry) if isinstance(entry, dict) else {}
        title = str(content.get("title", "")).strip()
        link = _yahoo_link(content)
        published = _parse_iso(content.get("pubDate") or content.get("displayTime"))
        provider = content.get("provider") or {}
        source = "Yahoo Finance"
        if isinstance(provider, dict):
            source = str(provider.get("displayName", "Yahoo Finance"))
        if title and is_safe_url(link):
            items.append({"symbol": symbol, "title": title, "link": link,
                          "source": source, "published": published})
    return items


def _yahoo_link(content: dict) -> str:
    for key in ("canonicalUrl", "clickThroughUrl"):
        val = content.get(key)
        if isinstance(val, dict):
            val = val.get("url", "")
        if isinstance(val, str) and val:
            return val
    return str(content.get("link", ""))


def _google_news(symbol: str, lang: str) -> list[dict]:
    """Google News RSS search — works for BIST tickers too (query by base name)."""
    query = symbol.replace(".IS", "") + (" hisse" if symbol.endswith(".IS") else " stock")
    params = (
        {"q": query, "hl": "tr", "gl": "TR", "ceid": "TR:tr"}
        if lang == "tr" or symbol.endswith(".IS")
        else {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    )
    try:
        resp = requests.get(
            config.GOOGLE_NEWS_RSS, params=params, timeout=config.REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (portfolio-dashboard)"},
        )
        resp.raise_for_status()
        root = SafeET.fromstring(resp.content)
    except Exception:
        return []
    items = []
    for node in root.iter("item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        source = (node.findtext("source") or "Google News").strip()
        published = _parse_rfc822(node.findtext("pubDate"))
        if title and is_safe_url(link):
            items.append({"symbol": symbol, "title": title, "link": link,
                          "source": source, "published": published})
        if len(items) >= config.NEWS_PER_SYMBOL:
            break
    return items


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _parse_iso(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return _EPOCH


def _parse_rfc822(value: object) -> datetime:
    if isinstance(value, str):
        try:
            parsed = parsedate_to_datetime(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError):
            pass
    return _EPOCH
