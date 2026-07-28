"""Streamlit entrypoint. Run with: streamlit run app.py"""

from __future__ import annotations

import streamlit as st

from portfoy import config, data, risk, storage
from portfoy.i18n import t
from portfoy.views import (
    alerts_page,
    compare_page,
    market_page,
    news_page,
    options_page,
    overview,
    positions,
    rotation_page,
)
from portfoy.views.common import inject_css

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def build_context(lang: str) -> dict:
    """Fetch everything each page needs once per rerun."""
    position_list = storage.load_portfolio()
    cash = storage.load_cash()
    symbols = tuple(p.symbol for p in position_list)
    quotes = data.get_quotes(symbols) if symbols else {}
    histories = {sym: data.get_history(sym) for sym in symbols}
    usdtry = data.get_usdtry()
    macro = data.get_macro_snapshot()
    cash_usd = risk.cash_totals(cash, usdtry)["usd"]
    metrics = risk.compute_metrics(position_list, quotes, histories, usdtry, cash_usd)
    earnings = {
        m.symbol: (data.get_next_earnings(m.symbol) if not m.symbol.endswith(".IS") else None)
        for m in metrics
    }
    vix = next((row["price"] for row in macro if row["symbol"] == "^VIX"), None)
    return {
        "lang": lang,
        "positions": position_list,
        "cash": cash,
        "quotes": quotes,
        "metrics": metrics,
        "totals": risk.portfolio_totals(metrics, usdtry, cash),
        "alerts": risk.build_alerts(metrics, earnings, vix),
        "macro": macro,
        "usdtry": usdtry,
    }


def main() -> None:
    inject_css()
    with st.sidebar:
        st.title("📊")
        choice = st.radio(t("language"), ["Türkçe", "English"], horizontal=True)
        lang = "tr" if choice == "Türkçe" else "en"
        page = st.radio(
            "Menu",
            [t("nav_overview", lang), t("nav_market", lang), t("nav_positions", lang),
             t("nav_alerts", lang), t("nav_compare", lang), t("nav_rotation", lang),
             t("nav_options", lang), t("nav_news", lang)],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button(t("refresh", lang), use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption(t("last_update", lang))
        st.caption(t("disclaimer", lang))

    if storage.is_demo():
        st.info(t("demo_banner", lang))
    ctx = build_context(lang)
    routes = {
        t("nav_overview", lang): overview.render,
        t("nav_market", lang): market_page.render,
        t("nav_positions", lang): positions.render,
        t("nav_alerts", lang): alerts_page.render,
        t("nav_compare", lang): compare_page.render,
        t("nav_rotation", lang): rotation_page.render,
        t("nav_options", lang): options_page.render,
        t("nav_news", lang): news_page.render,
    }
    routes.get(page, overview.render)(ctx)


if __name__ == "__main__":
    main()
