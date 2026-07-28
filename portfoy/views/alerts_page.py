"""Risk & Alerts page: full alert list + ATR stop suggestion table."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import config
from ..i18n import t
from .common import alert_card, hero


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("alerts_title", lang), t("alerts_intro", lang))

    if not ctx["metrics"]:
        st.info(t("empty_portfolio", lang))
        return

    alerts = ctx["alerts"]
    if not alerts:
        st.markdown(f":green[{t('no_alerts', lang)}]")
    for alert in alerts:
        alert_card(alert, lang)

    st.subheader(t("stop_table", lang))
    st.caption(t("stop_help", lang, mult=config.ATR_STOP_MULT, period=config.ATR_PERIOD))
    rows = [
        {
            t("symbol", lang): m.symbol,
            t("col_price", lang): round(m.price, 2),
            t("stop_line", lang): round(m.atr_stop, 2) if m.atr_stop else None,
            "RSI": round(m.rsi, 1) if m.rsi is not None else None,
            f"SMA{config.SMA_FAST}": round(m.sma_fast, 2) if m.sma_fast else None,
            f"SMA{config.SMA_SLOW}": round(m.sma_slow, 2) if m.sma_slow else None,
        }
        for m in ctx["metrics"]
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
