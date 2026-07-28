"""Performance page: the portfolio's return raced against other assets."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, config, data, performance
from ..i18n import t
from .common import fmt_money, hero, metric_card


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("cmp_title", lang), t("cmp_intro", lang))

    metrics = ctx["metrics"]
    totals = ctx["totals"]
    if not metrics and not ctx["cash"]:
        st.info(t("empty_portfolio", lang))
        return

    base, period = _controls(lang)
    results = _build_results(ctx, base, period)
    if not results:
        st.info(t("cmp_no_data", lang))
        return

    _verdict(results, lang, totals)

    st.subheader(t("cmp_chart", lang))
    st.plotly_chart(charts.compare_lines(results, lang), use_container_width=True)

    left, right = st.columns([1, 1])
    with left:
        st.subheader(t("cmp_ranking", lang))
        st.plotly_chart(charts.compare_bar(results, lang), use_container_width=True)
    with right:
        st.subheader(" ")
        _ranking_table(results, lang)

    _realized(ctx, lang)


def _controls(lang: str) -> tuple[str, str]:
    col1, col2 = st.columns([1, 2])
    base = col1.radio(t("cmp_base", lang), list(config.CASH_CURRENCIES), horizontal=True)
    period = col2.radio(
        t("cmp_period", lang), list(config.COMPARE_PERIODS),
        format_func=lambda key: t(key, lang), horizontal=True,
        index=list(config.COMPARE_PERIODS).index(config.DEFAULT_COMPARE_PERIOD),
    )
    return base, period


def _build_results(ctx: dict, base: str, period: str) -> list[performance.SeriesResult]:
    metrics = ctx["metrics"]
    symbols = [m.symbol for m in metrics]
    prices = {
        sym: data.get_history(sym, config.COMPARE_HISTORY_PERIOD)["Close"]
        for sym in symbols
        if not data.get_history(sym, config.COMPARE_HISTORY_PERIOD).empty
    }
    benchmarks = {}
    for sym in config.BENCHMARKS:
        hist = data.get_history(sym, config.COMPARE_HISTORY_PERIOD)
        if not hist.empty:
            benchmarks[sym] = hist["Close"]
    fx_hist = data.get_history(config.FX_USDTRY, config.COMPARE_HISTORY_PERIOD)
    usdtry = fx_hist["Close"] if not fx_hist.empty else pd.Series(dtype=float)
    if base == "TRY" and usdtry.empty:
        return []

    reference = next(iter(benchmarks.values()), None)
    start = (
        performance.window_start(performance.to_daily(reference).index, period)
        if reference is not None
        else None
    )

    portfolio = performance.portfolio_series(
        weights={m.symbol: m.weight for m in metrics},
        prices=prices,
        currencies={m.symbol: m.currency for m in metrics},
        base=base,
        usdtry=usdtry,
        start=start,
        cash_weight=ctx["totals"].get("cash_weight", 0.0),
    )
    return performance.compare(portfolio, benchmarks, base, usdtry, period)


def _verdict(results: list, lang: str, totals: dict) -> None:
    mine = next((r for r in results if r.key == "portfolio"), None)
    if mine is None:
        return
    others = [r for r in results if r.key != "portfolio"]
    beaten = sum(1 for r in others if mine.return_pct > r.return_pct)
    st.markdown(
        t("cmp_verdict_win", lang, beaten=beaten, total=len(others),
          value=f"{mine.return_pct:+.2f}")
    )
    cash_weight = totals.get("cash_weight", 0.0)
    if cash_weight >= 0.05:
        st.caption(t("cmp_cash_note", lang, value=f"{cash_weight * 100:.0f}"))


def _ranking_table(results: list, lang: str) -> None:
    mine = next((r for r in results if r.key == "portfolio"), None)
    base_return = mine.return_pct if mine else 0.0
    frame = pd.DataFrame(
        {
            t("cmp_rank_col", lang): list(range(1, len(results) + 1)),
            t("cmp_asset", lang): [r.label(lang) for r in results],
            t("cmp_return", lang): [r.return_pct / 100 for r in results],
            t("cmp_vs", lang): [(r.return_pct - base_return) / 100 for r in results],
        }
    )
    st.dataframe(
        frame.style
        .format({t("cmp_return", lang): "{:+.2%}", t("cmp_vs", lang): "{:+.2%}"})
        .map(_pct_color, subset=[t("cmp_return", lang), t("cmp_vs", lang)]),
        use_container_width=True, hide_index=True,
    )


def _realized(ctx: dict, lang: str) -> None:
    lang_totals = ctx["totals"]
    st.subheader(t("cmp_realized", lang))
    st.caption(t("cmp_realized_hint", lang))
    cols = st.columns(4)
    cards = [
        metric_card(t("invested", lang), fmt_money(lang_totals["invested_try"], "TRY")),
        metric_card(t("cash_total", lang), fmt_money(lang_totals["cash_try"], "TRY")),
        metric_card(t("total_value", lang), fmt_money(lang_totals["value_try"], "TRY")),
        metric_card(t("total_pnl", lang), fmt_money(lang_totals["pnl_usd"], "USD"),
                    lang_totals["pnl_pct"]),
    ]
    for col, card in zip(cols, cards, strict=True):
        col.markdown(card, unsafe_allow_html=True)


def _pct_color(value: float) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return ""
    if num > 0:
        return "color: #34d399"
    if num < 0:
        return "color: #f87171"
    return ""
