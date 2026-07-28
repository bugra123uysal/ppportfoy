"""Positions page: add / reduce / delete holdings, table, detail chart."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, config, data, storage
from ..i18n import t
from ..security import ValidationError
from .common import hero


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("nav_positions", lang), t("symbol_help", lang))
    _add_form(ctx)
    _cash_form(ctx)
    metrics = ctx["metrics"]
    if not metrics:
        st.info(t("empty_portfolio", lang))
        return
    _holdings_table(metrics, lang)
    _sell_and_delete(ctx)
    _detail_chart(ctx)


def _add_form(ctx: dict) -> None:
    lang = ctx["lang"]
    with st.expander(t("add_position", lang), expanded=not ctx["positions"]):
        with st.form("add_position", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.2, 1, 1])
            raw_symbol = c1.text_input(t("symbol", lang), placeholder="THYAO.IS / AAPL",
                                       max_chars=15, help=t("symbol_help", lang))
            quantity = c2.number_input(t("quantity", lang), min_value=0.0,
                                       step=1.0, format="%.4f")
            avg_cost = c3.number_input(t("avg_cost", lang), min_value=0.0,
                                       step=0.01, format="%.4f")
            notes = st.text_input(t("notes", lang), max_chars=300)
            if st.form_submit_button(t("add_btn", lang), type="primary"):
                _handle_add(ctx, raw_symbol, quantity, avg_cost, notes)


def _handle_add(ctx: dict, raw_symbol: str, quantity: float, avg_cost: float, notes: str) -> None:
    lang = ctx["lang"]
    try:
        position = storage.make_position(raw_symbol, quantity, avg_cost, notes)
    except ValidationError as exc:
        st.error(str(exc))
        return
    if not data.symbol_exists(position.symbol):
        st.warning(t("symbol_not_found", lang, symbol=position.symbol))
        return
    try:
        updated = storage.upsert_position(ctx["positions"], position)
    except ValidationError as exc:
        st.error(str(exc))
        return
    storage.save_portfolio(updated)
    st.success(t("added_ok", lang, symbol=position.symbol))
    st.rerun()


def _cash_form(ctx: dict) -> None:
    lang = ctx["lang"]
    balances = {c.currency: c.amount for c in ctx["cash"]}
    with st.expander(t("cash_section", lang), expanded=False):
        st.caption(t("cash_hint", lang))
        with st.form("cash_form"):
            c1, c2, c3 = st.columns([1, 1.4, 1])
            currency = c1.selectbox(t("cash_currency", lang), config.CASH_CURRENCIES)
            amount = c2.number_input(
                t("cash_amount", lang), min_value=0.0,
                value=float(balances.get(currency, 0.0)), step=100.0, format="%.2f",
            )
            c3.write("")
            c3.write("")
            if c3.form_submit_button(t("cash_save", lang), type="primary"):
                _handle_cash(ctx, currency, amount)
        if balances:
            st.write(" · ".join(
                f"**{cur}** {amt:,.2f}" for cur, amt in sorted(balances.items())
            ))


def _handle_cash(ctx: dict, currency: str, amount: float) -> None:
    try:
        updated = storage.set_cash(ctx["cash"], currency, amount)
    except ValidationError as exc:
        st.error(str(exc))
        return
    storage.save_cash(updated)
    st.success(t("cash_saved", ctx["lang"]))
    st.rerun()


def _holdings_table(metrics, lang: str) -> None:
    st.subheader(t("holdings", lang))
    frame = pd.DataFrame(
        {
            t("symbol", lang): [m.symbol for m in metrics],
            t("quantity", lang): [m.quantity for m in metrics],
            t("avg_cost", lang): [m.avg_cost for m in metrics],
            t("col_price", lang): [m.price for m in metrics],
            t("col_daily", lang): [m.change_pct / 100 for m in metrics],
            t("col_value", lang): [m.value for m in metrics],
            t("col_pnl", lang): [m.pnl for m in metrics],
            t("col_pnl_pct", lang): [m.pnl_pct / 100 for m in metrics],
            t("col_weight", lang): [m.weight for m in metrics],
        }
    )
    # Single .format() call: chained calls reset previously formatted columns
    # to the default renderer on pandas 3.x.
    styled = (
        frame.style
        .format({t("quantity", lang): "{:,.2f}", t("avg_cost", lang): "{:,.2f}",
                 t("col_price", lang): "{:,.2f}", t("col_value", lang): "{:,.0f}",
                 t("col_pnl", lang): "{:+,.0f}", t("col_daily", lang): "{:+.2%}",
                 t("col_pnl_pct", lang): "{:+.2%}", t("col_weight", lang): "{:.1%}"})
        .map(_pnl_color, subset=[t("col_daily", lang), t("col_pnl", lang), t("col_pnl_pct", lang)])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


def _pnl_color(value: float) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return ""
    if num > 0:
        return "color: #34d399"
    if num < 0:
        return "color: #f87171"
    return ""


def _sell_and_delete(ctx: dict) -> None:
    lang = ctx["lang"]
    symbols = [p.symbol for p in ctx["positions"]]
    with st.expander(t("sell_reduce", lang)):
        c1, c2, c3 = st.columns([1.2, 1, 1])
        target = c1.selectbox(t("symbol", lang), symbols, key="sell_symbol")
        current = next((p for p in ctx["positions"] if p.symbol == target), None)
        max_qty = float(current.quantity) if current else 0.0
        qty = c2.number_input(t("sell_qty", lang), min_value=0.0, max_value=max_qty,
                              value=0.0, step=1.0, format="%.4f", key="sell_qty")
        c3.write("")
        c3.write("")
        if c3.button(t("sell_btn", lang), key="sell_btn") and current and qty > 0:
            updated = storage.reduce_position(ctx["positions"], target, qty)
            storage.save_portfolio(updated)
            st.success(t("removed_ok", lang))
            st.rerun()
        if st.button(t("delete_btn", lang), key="delete_btn") and current:
            updated = storage.remove_position(ctx["positions"], target)
            storage.save_portfolio(updated)
            st.success(t("removed_ok", lang))
            st.rerun()


def _detail_chart(ctx: dict) -> None:
    lang = ctx["lang"]
    metrics = ctx["metrics"]
    st.subheader(t("detail_chart", lang))
    symbol = st.selectbox(t("choose_symbol", lang), [m.symbol for m in metrics])
    chosen = next((m for m in metrics if m.symbol == symbol), None)
    if chosen is None:
        return
    hist = data.get_history(symbol, config.DEFAULT_HISTORY_PERIOD)
    if hist.empty:
        st.info(t("data_error", lang))
        return
    st.plotly_chart(
        charts.price_chart(hist, symbol, chosen.avg_cost, chosen.atr_stop, lang),
        use_container_width=True,
    )
