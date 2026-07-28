"""Market Compass page: the 5 layers of reading the market + the calendar.

Each layer shows live data, a short professional summary and a
plain-language ("explain like I'm five") expander.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from .. import charts, config, data
from ..breadth import build_snapshot, pct_above_ma
from ..calendar_events import upcoming_events
from ..i18n import t
from ..indicators import last_value, sma
from ..rotation import LAGGING, LEADING, build_rotation
from ..sentiment import build_score
from .common import hero, macro_strip, metric_card


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("mkt_title", lang), t("mkt_intro", lang))
    _layer_macro(ctx, lang)
    closes = data.get_daily_closes(config.BREADTH_UNIVERSE)
    snapshot = _layer_internals(closes, lang)
    _layer_sentiment(ctx, snapshot, lang)
    _layer_money_flow(lang)
    _layer_single_stock(ctx, lang)
    _calendar(ctx, lang)


def _simple(lang: str, key: str) -> None:
    with st.expander(t("mkt_simple", lang)):
        st.markdown(t(key, lang))


# --- 1. macro ---------------------------------------------------------------

def _layer_macro(ctx: dict, lang: str) -> None:
    st.subheader(t("mkt_l1_title", lang))
    st.caption(t("mkt_l1_summary", lang))
    if ctx["macro"]:
        macro_strip(ctx["macro"])
    else:
        st.info(t("data_error", lang))
    _simple(lang, "mkt_l1_simple")
    st.divider()


# --- 2. internals / breadth -------------------------------------------------

def _layer_internals(closes, lang: str):
    st.subheader(t("mkt_l2_title", lang))
    snapshot = build_snapshot(closes)
    if snapshot is None:
        st.info(t("data_error", lang))
        st.divider()
        return None
    st.caption(t("mkt_l2_summary", lang, size=snapshot.sample_size))
    cols = st.columns(4)
    cards = [
        metric_card(t("mkt_l2_pct50", lang), f"%{snapshot.pct_above_50:.0f}"),
        metric_card(t("mkt_l2_pct200", lang), f"%{snapshot.pct_above_200:.0f}"),
        metric_card(t("mkt_l2_ad", lang), f"{snapshot.advancers} / {snapshot.decliners}"),
        metric_card(t("mkt_l2_hl", lang), f"{snapshot.new_high_20d} / {snapshot.new_low_20d}"),
    ]
    for col, card in zip(cols, cards, strict=True):
        col.markdown(card, unsafe_allow_html=True)
    st.markdown(t(f"mkt_l2_{snapshot.health}", lang))
    st.plotly_chart(
        charts.breadth_history(pct_above_ma(closes, 50), pct_above_ma(closes, 200), lang),
        use_container_width=True,
    )
    _simple(lang, "mkt_l2_simple")
    st.divider()
    return snapshot


# --- 3. sentiment -----------------------------------------------------------

def _layer_sentiment(ctx: dict, snapshot, lang: str) -> None:
    st.subheader(t("mkt_l3_title", lang))
    st.caption(t("mkt_l3_summary", lang))

    vix = next((row["price"] for row in ctx["macro"] if row["symbol"] == "^VIX"), None)
    spx = data.get_history("^GSPC")
    price = last_value(spx["Close"]) if not spx.empty else None
    spx_sma = (
        last_value(sma(spx["Close"], config.SENT_MOMENTUM_SMA)) if not spx.empty else None
    )
    spy_options = data.get_option_activity("SPY")
    put_call = spy_options.put_call_ratio if spy_options else None
    pct_200 = snapshot.pct_above_200 if snapshot else None

    score = build_score(vix=vix, price=price, sma=spx_sma,
                        pct_above_200=pct_200, put_call=put_call)
    if score is None:
        st.info(t("data_error", lang))
        st.divider()
        return

    left, right = st.columns([1.1, 1])
    with left:
        st.plotly_chart(
            charts.sentiment_gauge(score.composite, t(f"sent_{score.label}", lang)),
            use_container_width=True,
        )
    with right:
        for name, value in score.components.items():
            st.markdown(f"**{t(f'sent_comp_{name}', lang)}**: {value:.0f} / 100")
        if vix is not None:
            zone = ("vix_calm" if vix < 20 else "vix_tense" if vix < 30 else "vix_panic")
            st.caption(t("mkt_l3_vix_zone", lang, vix=f"{vix:.1f}", zone=t(zone, lang)))
    _simple(lang, "mkt_l3_simple")
    st.divider()


# --- 4. money flow ----------------------------------------------------------

def _layer_money_flow(lang: str) -> None:
    st.subheader(t("mkt_l4_title", lang))
    st.caption(t("mkt_l4_summary", lang))
    closes = data.get_weekly_closes(tuple([config.RRG_BENCHMARK, *config.SECTOR_ETFS]))
    points = (
        build_rotation(closes, dict(config.SECTOR_ETFS),
                       reference=list(config.SECTOR_ETFS))
        if not closes.empty else []
    )
    if not points:
        st.info(t("data_error", lang))
    else:
        leading = [f"{p.symbol} ({p.label(lang)})" for p in points if p.quadrant == LEADING]
        lagging = [f"{p.symbol} ({p.label(lang)})" for p in points if p.quadrant == LAGGING]
        col1, col2 = st.columns(2)
        col1.markdown(f"**{t('mkt_l4_leading', lang)}**")
        col1.markdown("🟢 " + (" · ".join(leading) or "—"))
        col2.markdown(f"**{t('mkt_l4_lagging', lang)}**")
        col2.markdown("🔴 " + (" · ".join(lagging) or "—"))
        st.caption(f"→ {t('nav_rotation', lang)}")
    _simple(lang, "mkt_l4_simple")
    st.divider()


# --- 5. single stock --------------------------------------------------------

def _layer_single_stock(ctx: dict, lang: str) -> None:
    st.subheader(t("mkt_l5_title", lang))
    st.caption(t("mkt_l5_summary", lang))
    metrics = ctx["metrics"]
    if not metrics:
        st.info(t("empty_portfolio", lang))
    else:
        alerts = ctx["alerts"]
        crit = sum(1 for a in alerts if a.severity == "crit")
        below_200 = [m.symbol for m in metrics
                     if m.sma_slow is not None and m.price < m.sma_slow]
        soon = [a.params.get("symbol") for a in alerts if a.key == "al_earnings"]
        cols = st.columns(3)
        cards = [
            metric_card(t("mkt_l5_alerts", lang),
                        f"{len(alerts)} · " + t("mkt_l5_crit", lang, n=crit)),
            metric_card(t("mkt_l5_below200", lang),
                        ", ".join(below_200) or t("mkt_l5_none", lang)),
            metric_card(t("mkt_l5_earnings_soon", lang),
                        ", ".join(s for s in soon if s) or t("mkt_l5_none", lang)),
        ]
        for col, card in zip(cols, cards, strict=True):
            col.markdown(card, unsafe_allow_html=True)
    _simple(lang, "mkt_l5_simple")
    st.divider()


# --- economic calendar ------------------------------------------------------

def _calendar(ctx: dict, lang: str) -> None:
    st.subheader(t("mkt_cal_title", lang))
    st.caption(t("mkt_cal_summary", lang))
    today = date.today()
    earnings = {
        m.symbol: data.get_next_earnings(m.symbol)
        for m in ctx["metrics"] if not m.symbol.endswith(".IS")
    }
    events = upcoming_events(today, earnings)
    if not events:
        st.info(t("ev_none", lang, n=config.CALENDAR_LOOKAHEAD_DAYS))
    for event in events:
        label = (t("ev_earnings", lang, symbol=event.symbol)
                 if event.kind == "earnings" else t(f"ev_{event.kind}", lang))
        days = event.days_left(today)
        when = (t("ev_today", lang) if days == 0 else t("ev_days_left", lang, n=days))
        st.markdown(
            f"- **{event.when.strftime('%d.%m.%Y')}** — {label} · _{when}_"
        )
    _simple(lang, "mkt_cal_simple")
