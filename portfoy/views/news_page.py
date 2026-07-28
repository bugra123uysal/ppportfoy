"""News page: merged Yahoo + Google News feed for every holding."""

from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from ..i18n import t
from ..news import get_news_for
from ..security import escape_html, is_safe_url
from .common import hero


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("news_title", lang), t("news_intro", lang))

    symbols = [p.symbol for p in ctx["positions"]]
    if not symbols:
        st.info(t("empty_portfolio", lang))
        return

    choice = st.selectbox(t("news_filter", lang), [t("news_all", lang), *symbols])
    targets = symbols if choice == t("news_all", lang) else [choice]

    with st.spinner("..."):
        items = []
        for sym in targets:
            items.extend(get_news_for(sym, lang))
    items.sort(key=lambda x: x["published"], reverse=True)

    if not items:
        st.info(t("news_none", lang))
        return
    for item in items[:40]:
        _news_card(item, lang)


def _news_card(item: dict, lang: str) -> None:
    link = item["link"]
    if not is_safe_url(link):
        return
    age = _age_text(item["published"], lang)
    st.markdown(
        f'<div class="news-card">'
        f'<span class="news-sym">{escape_html(item["symbol"])}</span>'
        f'<a href="{escape_html(link)}" target="_blank" rel="noopener noreferrer">'
        f'{escape_html(item["title"])}</a>'
        f'<div class="news-meta">{escape_html(item["source"])}{age}</div></div>',
        unsafe_allow_html=True,
    )


def _age_text(published: datetime, lang: str) -> str:
    if published.year <= 1970:
        return ""
    delta = datetime.now(UTC) - published
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return " · " + ("az önce" if lang == "tr" else "just now")
    if hours < 24:
        return f" · {hours} " + ("saat önce" if lang == "tr" else "h ago")
    days = hours // 24
    return f" · {days} " + ("gün önce" if lang == "tr" else "d ago")
