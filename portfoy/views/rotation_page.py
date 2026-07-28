"""Sector rotation page: RRG map, quadrant moves, performance ranking."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, config, data
from ..i18n import t
from ..rotation import LAGGING, LEADING, build_rotation, is_clockwise
from .common import hero

_DEFENSIVE = {"XLP", "XLU", "XLV", "XLRE"}
_CYCLICAL = {"XLK", "XLY", "XLI", "XLF", "XLB", "XLE", "XLC"}

_PERF_FIELDS = {"rot_1w": "perf_1w", "rot_1m": "perf_1m", "rot_3m": "perf_3m"}


def render(ctx: dict) -> None:
    lang = ctx["lang"]
    hero(t("rot_title", lang), t("rot_intro", lang))

    include_mine = st.checkbox(t("rot_include_mine", lang), value=False,
                               help=t("rot_mine_hint", lang))
    points = _load_rotation(ctx, include_mine)
    if not points:
        st.info(t("rot_loading_error", lang))
        return

    sectors = [p for p in points if p.symbol in config.SECTOR_ETFS]
    _summary(sectors or points, lang)

    st.subheader(t("rot_chart_title", lang))
    st.plotly_chart(charts.rotation_rrg(points, lang), use_container_width=True)
    with st.expander(t("rot_how_to", lang)):
        st.markdown(t("rot_how_to_body", lang))

    _moves(points, lang)
    _performance(sectors or points, lang)


def _load_rotation(ctx: dict, include_mine: bool):
    symbols = [config.RRG_BENCHMARK, *config.SECTOR_ETFS]
    labels = dict(config.SECTOR_ETFS)
    if include_mine:
        # BIST tickers trade in TRY against a TRY index, so they are not
        # comparable to an SPY-based RRG; only US holdings are added.
        mine = [p.symbol for p in ctx["positions"]
                if not p.symbol.endswith(".IS") and p.symbol not in symbols]
        symbols.extend(mine)
        labels.update({sym: ("Portföyüm", "My holding") for sym in mine})
    closes = data.get_weekly_closes(tuple(symbols))
    if closes.empty:
        return []
    # Sectors always define the scale, so the map does not shift when the
    # user's (far more volatile) holdings are overlaid on top of it.
    return build_rotation(closes, labels, reference=list(config.SECTOR_ETFS))


def _summary(points: list, lang: str) -> None:
    leading = [p.symbol for p in points if p.quadrant == LEADING]
    lagging = [p.symbol for p in points if p.quadrant == LAGGING]
    cyclical_lead = len(set(leading) & _CYCLICAL)
    defensive_lead = len(set(leading) & _DEFENSIVE)
    if cyclical_lead > defensive_lead:
        direction = t("rot_risk_on", lang)
    elif defensive_lead > cyclical_lead:
        direction = t("rot_risk_off", lang)
    else:
        direction = t("rot_mixed", lang)
    st.markdown(
        t("rot_summary", lang,
          leading=", ".join(leading) or "—",
          lagging=", ".join(lagging) or "—",
          direction=direction)
    )


def _moves(points: list, lang: str) -> None:
    st.subheader(t("rot_moves", lang))
    movers = [p for p in points if p.has_moved]
    if not movers:
        st.caption(t("rot_no_moves", lang))
        return
    for point in movers:
        note = t("rot_healthy" if is_clockwise(point.prev_quadrant, point.quadrant)
                 else "rot_unusual", lang)
        st.markdown(
            t("rot_moved", lang, symbol=point.symbol, label=point.label(lang),
              frm=t(f"q_{point.prev_quadrant}", lang), to=t(f"q_{point.quadrant}", lang))
            + f"  ·  _{note}_"
        )


def _performance(points: list, lang: str) -> None:
    st.subheader(t("rot_table", lang))
    choice = st.radio(
        t("rot_perf_pick", lang), list(_PERF_FIELDS),
        format_func=lambda key: t(key, lang), horizontal=True, index=1,
    )
    field = _PERF_FIELDS[choice]
    left, right = st.columns([1.3, 1])
    with left:
        st.plotly_chart(charts.rotation_perf_bar(points, lang, field), use_container_width=True)
    with right:
        frame = pd.DataFrame(
            {
                t("rot_sector", lang): [f"{p.symbol} · {p.label(lang)}" for p in points],
                t("rot_zone", lang): [t(f"q_{p.quadrant}", lang) for p in points],
                t("rot_1w", lang): [p.perf_1w / 100 for p in points],
                t("rot_1m", lang): [p.perf_1m / 100 for p in points],
                t("rot_3m", lang): [p.perf_3m / 100 for p in points],
            }
        ).sort_values(t(choice, lang), ascending=False)
        pct_cols = [t("rot_1w", lang), t("rot_1m", lang), t("rot_3m", lang)]
        st.dataframe(
            frame.style.format({col: "{:+.2%}" for col in pct_cols})
            .map(_perf_color, subset=pct_cols),
            use_container_width=True, hide_index=True,
        )


def _perf_color(value: float) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return ""
    if num > 0:
        return "color: #34d399"
    if num < 0:
        return "color: #f87171"
    return ""
