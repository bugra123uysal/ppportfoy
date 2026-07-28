"""Overview page: macro strip, portfolio totals, allocation, alert summary."""

from __future__ import annotations

import streamlit as st

from .. import charts, storage
from ..i18n import t
from .common import alert_card, fmt_money, hero, macro_strip, metric_card


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("app_title", lang), t("disclaimer", lang))

    st.subheader(t("macro_strip", lang))
    if ctx["macro"]:
        macro_strip(ctx["macro"])
    else:
        st.info(t("data_error", lang))

    metrics = ctx["metrics"]
    totals = ctx["totals"]
    if not metrics and not ctx["cash"]:
        st.info(t("empty_portfolio", lang))
        return

    usd = f"${totals['value_usd']:,.0f}"
    try_val = f"₺{totals['value_try']:,.0f}"
    cols = st.columns(5)
    cards = [
        metric_card(t("total_value", lang), f"{try_val}  ·  {usd}"),
        metric_card(t("invested", lang), fmt_money(totals["invested_try"], "TRY")),
        metric_card(t("cash_total", lang), fmt_money(totals["cash_try"], "TRY")),
        metric_card(t("total_pnl", lang), fmt_money(totals["pnl_usd"], "USD"), totals["pnl_pct"]),
        metric_card(t("daily_change", lang), f"{totals['daily_pct']:+.2f}%", totals["daily_pct"]),
    ]
    for col, card in zip(cols, cards, strict=True):
        col.markdown(card, unsafe_allow_html=True)

    if not metrics:
        return

    st.write("")
    left, right = st.columns([1, 1.2])
    with left:
        st.subheader(t("allocation", lang))
        st.plotly_chart(
            charts.allocation_with_cash_donut(
                metrics, totals["cash_usd"], t("cash_total", lang)
            ),
            use_container_width=True,
        )
    with right:
        st.subheader(t("pnl_by_position", lang))
        st.plotly_chart(charts.pnl_bar(metrics), use_container_width=True)

    # Daily snapshot + history chart
    history = storage.append_snapshot(totals["value_try"], totals["value_usd"])
    if len(history) > 1:
        st.subheader(t("value_history", lang))
        st.plotly_chart(charts.history_line(history, lang), use_container_width=True)
    else:
        st.caption(t("history_hint", lang))

    st.subheader(t("risk_summary", lang))
    urgent = [a for a in ctx["alerts"] if a.severity in ("crit", "warn")]
    if not urgent:
        st.markdown(f":green[{t('no_alerts', lang)}]")
    else:
        for alert in urgent[:6]:
            alert_card(alert, lang)
        st.caption(t("see_alerts", lang))
