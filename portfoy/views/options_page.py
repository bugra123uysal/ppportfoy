"""Options radar page: call/put volume ranking across liquid US names."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, config, data
from ..i18n import t
from ..options import OptionActivity, pcr_mood, rank_by_volume
from .common import hero, metric_card


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("opt_title", lang), t("opt_intro", lang))
    st.caption(t("opt_note", lang))

    activities = _scan(ctx, lang)
    if not activities:
        st.info(t("opt_no_data", lang))
        return

    _summary_cards(activities, lang)

    st.subheader(t("opt_chart_title", lang))
    st.plotly_chart(charts.options_volume_bar(activities, lang), use_container_width=True)

    _ranking_table(activities, lang)
    st.caption(t("opt_pcr_help", lang, bear=config.PCR_BEARISH, bull=config.PCR_BULLISH))
    _detail(activities, lang)


def _scan(ctx: dict, lang: str) -> list[OptionActivity]:
    own_us = [p.symbol for p in ctx["positions"] if not p.symbol.endswith(".IS")]
    universe = list(dict.fromkeys([*config.OPTIONS_UNIVERSE, *own_us]))
    results = []
    progress = st.progress(0.0, text=t("opt_scanning", lang))
    for i, symbol in enumerate(universe):
        activity = data.get_option_activity(symbol)
        if activity is not None:
            results.append(activity)
        progress.progress((i + 1) / len(universe), text=t("opt_scanning", lang))
    progress.empty()
    return rank_by_volume(results)


def _summary_cards(activities: list[OptionActivity], lang: str) -> None:
    busiest = activities[0]
    with_pcr = [a for a in activities if a.put_call_ratio is not None]
    cols = st.columns(3)
    cards = [
        metric_card(t("opt_busiest", lang),
                    f"{busiest.symbol} · {busiest.total_volume:,.0f}"),
    ]
    if with_pcr:
        most_bearish = max(with_pcr, key=lambda a: a.put_call_ratio)
        most_bullish = min(with_pcr, key=lambda a: a.put_call_ratio)
        cards.append(metric_card(t("opt_most_bearish", lang),
                                 f"{most_bearish.symbol} · {most_bearish.put_call_ratio:.2f}"))
        cards.append(metric_card(t("opt_most_bullish", lang),
                                 f"{most_bullish.symbol} · {most_bullish.put_call_ratio:.2f}"))
    for col, card in zip(cols, cards, strict=False):
        col.markdown(card, unsafe_allow_html=True)
    st.write("")


def _ranking_table(activities: list[OptionActivity], lang: str) -> None:
    st.subheader(t("opt_table_title", lang))
    frame = pd.DataFrame(
        {
            t("symbol", lang): [a.symbol for a in activities],
            t("opt_col_expiry", lang): [a.expiry for a in activities],
            t("opt_col_call", lang): [a.call_volume for a in activities],
            t("opt_col_put", lang): [a.put_volume for a in activities],
            t("opt_col_total", lang): [a.total_volume for a in activities],
            t("opt_col_pcr", lang): [
                round(a.put_call_ratio, 2) if a.put_call_ratio is not None else None
                for a in activities
            ],
            t("opt_col_oi", lang): [a.call_oi + a.put_oi for a in activities],
            t("opt_col_mood", lang): [
                t(f"mood_{pcr_mood(a.put_call_ratio)}", lang) for a in activities
            ],
        }
    )
    int_cols = [t("opt_col_call", lang), t("opt_col_put", lang),
                t("opt_col_total", lang), t("opt_col_oi", lang)]
    st.dataframe(
        frame.style.format({c: "{:,.0f}" for c in int_cols}),
        use_container_width=True, hide_index=True,
    )


def _detail(activities: list[OptionActivity], lang: str) -> None:
    st.subheader(t("opt_detail", lang))
    chosen_symbol = st.selectbox(t("opt_detail_pick", lang), [a.symbol for a in activities])
    chosen = next((a for a in activities if a.symbol == chosen_symbol), None)
    if chosen is None or not chosen.top_contracts:
        st.info(t("opt_no_data", lang))
        return
    st.markdown(t("opt_detail_title", lang, symbol=chosen.symbol, expiry=chosen.expiry))
    frame = pd.DataFrame(
        {
            t("opt_col_type", lang): [c["type"] for c in chosen.top_contracts],
            t("opt_col_strike", lang): [c["strike"] for c in chosen.top_contracts],
            t("opt_col_last", lang): [c["last"] for c in chosen.top_contracts],
            t("opt_col_total", lang): [c["volume"] for c in chosen.top_contracts],
            t("opt_col_oi", lang): [c["oi"] for c in chosen.top_contracts],
            t("opt_col_iv", lang): [c["iv"] for c in chosen.top_contracts],
        }
    )
    st.dataframe(
        frame.style
        .format({t("opt_col_strike", lang): "{:,.2f}", t("opt_col_last", lang): "{:,.2f}",
                 t("opt_col_total", lang): "{:,.0f}", t("opt_col_oi", lang): "{:,.0f}",
                 t("opt_col_iv", lang): "{:.0%}"})
        .map(_type_color, subset=[t("opt_col_type", lang)]),
        use_container_width=True, hide_index=True,
    )


def _type_color(value: str) -> str:
    if value == "CALL":
        return "color: #34d399"
    if value == "PUT":
        return "color: #f87171"
    return ""
