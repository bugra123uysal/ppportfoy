"""Plotly figure builders. Dark theme tuned to the app's CSS palette."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import config
from .options import OptionActivity
from .performance import SeriesResult
from .risk import PositionMetrics
from .rotation import IMPROVING, LAGGING, LEADING, WEAKENING, SectorRotation

_BG = "rgba(0,0,0,0)"
_GRID = "rgba(148,163,184,0.12)"
_TEXT = "#cbd5e1"
_GREEN = "#34d399"
_RED = "#f87171"
_ACCENT = "#818cf8"
_GOLD = "#fbbf24"

_PIE_COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f87171", "#38bdf8",
               "#a78bfa", "#fb923c", "#4ade80", "#f472b6", "#94a3b8"]


def _base_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=dict(color=_TEXT, family="Segoe UI, sans-serif", size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor=_GRID, zeroline=False),
        yaxis=dict(gridcolor=_GRID, zeroline=False),
        legend=dict(orientation="h", y=1.08, x=0, bgcolor=_BG),
        hoverlabel=dict(bgcolor="#1e293b", font_color="#e2e8f0"),
    )
    return fig


def price_chart(
    hist: pd.DataFrame, symbol: str, avg_cost: float, atr_stop: float | None, lang: str
) -> go.Figure:
    """Candlesticks + SMA50/200 + the user's cost line + suggested stop."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name=symbol,
        increasing_line_color=_GREEN, decreasing_line_color=_RED,
        increasing_fillcolor=_GREEN, decreasing_fillcolor=_RED,
    ))
    close = hist["Close"]
    sma_specs = ((config.SMA_FAST, _ACCENT, "dot"), (config.SMA_SLOW, _GOLD, "dash"))
    for period, color, dash in sma_specs:
        line = close.rolling(period, min_periods=period).mean()
        if line.notna().any():
            fig.add_trace(go.Scatter(
                x=hist.index, y=line, name=f"SMA {period}",
                line=dict(color=color, width=1.4, dash=dash), hoverinfo="skip",
            ))
    cost_label = "Maliyet" if lang == "tr" else "Cost"
    fig.add_hline(y=avg_cost, line_color="#38bdf8", line_width=1.2, line_dash="dashdot",
                  annotation_text=f"{cost_label}: {avg_cost:,.2f}",
                  annotation_font_color="#38bdf8")
    if atr_stop is not None:
        stop_label = "Stop" if lang == "tr" else "Stop"
        fig.add_hline(y=atr_stop, line_color=_RED, line_width=1.2, line_dash="dot",
                      annotation_text=f"{stop_label}: {atr_stop:,.2f}",
                      annotation_font_color=_RED, annotation_position="bottom right")
    fig.update_layout(xaxis_rangeslider_visible=False)
    return _base_layout(fig, height=430)


def allocation_donut(metrics: list[PositionMetrics]) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=[m.symbol for m in metrics],
        values=[round(m.value_usd, 2) for m in metrics],
        hole=0.62,
        marker=dict(colors=_PIE_COLORS[: len(metrics)] or _PIE_COLORS,
                    line=dict(color="#0f172a", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="%{label}: $%{value:,.0f} (%{percent})<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return _base_layout(fig, height=330)


def pnl_bar(metrics: list[PositionMetrics]) -> go.Figure:
    ordered = sorted(metrics, key=lambda m: m.pnl_pct)
    colors = [_GREEN if m.pnl_pct >= 0 else _RED for m in ordered]
    fig = go.Figure(go.Bar(
        x=[round(m.pnl_pct, 2) for m in ordered],
        y=[m.symbol for m in ordered],
        orientation="h", marker_color=colors,
        text=[f"{m.pnl_pct:+.1f}%" for m in ordered],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _base_layout(fig, height=max(220, 40 * len(ordered) + 80))


_QUADRANT_FILL = {
    LEADING: "rgba(52,211,153,0.07)",
    WEAKENING: "rgba(251,191,36,0.07)",
    LAGGING: "rgba(248,113,113,0.07)",
    IMPROVING: "rgba(56,189,248,0.07)",
}
_QUADRANT_TEXT = {
    LEADING: ("#34d399", "LİDER", "LEADING"),
    WEAKENING: ("#fbbf24", "ZAYIFLAYAN", "WEAKENING"),
    LAGGING: ("#f87171", "GERİDE", "LAGGING"),
    IMPROVING: ("#38bdf8", "İYİLEŞEN", "IMPROVING"),
}

_ROTATION_COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f87171", "#38bdf8", "#a78bfa",
                    "#fb923c", "#4ade80", "#f472b6", "#22d3ee", "#e879f9", "#94a3b8"]


def rotation_rrg(points: list[SectorRotation], lang: str) -> go.Figure:
    """Relative Rotation Graph: a tail per sector with an arrowhead at 'now'."""
    fig = _base_layout(go.Figure(), height=560)
    if not points:
        return fig

    bounds = _rrg_bounds(points)
    _add_quadrants(fig, bounds, lang)

    for index, point in enumerate(points):
        color = _ROTATION_COLORS[index % len(_ROTATION_COLORS)]
        steps = len(point.tail_x)
        # Tail fades in and thickens toward the current week.
        fig.add_trace(go.Scatter(
            x=point.tail_x, y=point.tail_y, mode="lines+markers",
            name=f"{point.symbol} · {point.label(lang)}",
            line=dict(color=color, width=2, shape="spline"),
            marker=dict(
                color=color, size=[4 + 5 * i / max(steps - 1, 1) for i in range(steps)],
                opacity=[0.3 + 0.7 * i / max(steps - 1, 1) for i in range(steps)],
                line=dict(width=0),
            ),
            customdata=[point.label(lang)] * steps,
            hovertemplate=(
                f"<b>{point.symbol}</b> — %{{customdata}}<br>"
                "RS-Ratio: %{x:.2f}<br>RS-Momentum: %{y:.2f}<extra></extra>"
            ),
        ))
        # Real arrowhead from last week's point to the current one.
        fig.add_annotation(
            x=point.tail_x[-1], y=point.tail_y[-1],
            ax=point.tail_x[-2], ay=point.tail_y[-2],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.3, arrowwidth=2.4, arrowcolor=color,
            text="",
        )
        fig.add_annotation(
            x=point.tail_x[-1], y=point.tail_y[-1], text=f"<b>{point.symbol}</b>",
            showarrow=False, yshift=14, font=dict(color=color, size=11),
        )

    fig.add_hline(y=100, line_color="rgba(148,163,184,0.45)", line_width=1)
    fig.add_vline(x=100, line_color="rgba(148,163,184,0.45)", line_width=1)
    strength_title = "Göreceli Güç" if lang == "tr" else "Relative Strength"
    fig.update_layout(
        xaxis=dict(range=[bounds[0], bounds[1]], title=f"RS-Ratio → {strength_title}"),
        yaxis=dict(range=[bounds[2], bounds[3]], title="RS-Momentum ↑ Momentum"),
        legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top",
                    font=dict(size=10)),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def _rrg_bounds(points: list[SectorRotation]) -> tuple[float, float, float, float]:
    """Square axis ranges centred on 100 so the four quadrants stay comparable."""
    values = [abs(v - 100) for p in points for v in (*p.tail_x, *p.tail_y)]
    span = max(max(values, default=1.0) * 1.15, 1.0)
    return 100 - span, 100 + span, 100 - span, 100 + span


def _add_quadrants(fig: go.Figure, bounds: tuple[float, float, float, float], lang: str) -> None:
    x0, x1, y0, y1 = bounds
    rects = {
        LEADING: (100, x1, 100, y1),
        WEAKENING: (100, x1, y0, 100),
        LAGGING: (x0, 100, y0, 100),
        IMPROVING: (x0, 100, 100, y1),
    }
    for quadrant, (rx0, rx1, ry0, ry1) in rects.items():
        fig.add_shape(type="rect", x0=rx0, x1=rx1, y0=ry0, y1=ry1,
                      fillcolor=_QUADRANT_FILL[quadrant], line_width=0, layer="below")
        color, label_tr, label_en = _QUADRANT_TEXT[quadrant]
        fig.add_annotation(
            x=(rx0 + rx1) / 2, y=ry1 - (ry1 - ry0) * 0.06,
            text=label_tr if lang == "tr" else label_en,
            showarrow=False, font=dict(color=color, size=11), opacity=0.75,
        )


def rotation_perf_bar(points: list[SectorRotation], lang: str, field: str = "perf_1m") -> go.Figure:
    """Sector performance ranking — the 'money is flowing here' bar chart."""
    ordered = sorted(points, key=lambda p: getattr(p, field))
    values = [round(getattr(p, field), 2) for p in ordered]
    colors = [_GREEN if v >= 0 else _RED for v in values]
    fig = go.Figure(go.Bar(
        x=values,
        y=[f"{p.symbol} · {p.label(lang)}" for p in ordered],
        orientation="h", marker_color=colors,
        text=[f"{v:+.1f}%" for v in values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _base_layout(fig, height=max(300, 34 * len(ordered) + 90))


_COMPARE_COLORS = ["#34d399", "#fbbf24", "#f87171", "#38bdf8", "#a78bfa", "#fb923c", "#94a3b8"]
_PORTFOLIO_COLOR = "#818cf8"


def compare_lines(results: list[SeriesResult], lang: str) -> go.Figure:
    """Rebased-to-100 race chart: the portfolio against every benchmark."""
    fig = _base_layout(go.Figure(), height=430)
    others = 0
    for result in results:
        is_portfolio = result.key == "portfolio"
        if is_portfolio:
            color, width = _PORTFOLIO_COLOR, 3.4
        else:
            color, width = _COMPARE_COLORS[others % len(_COMPARE_COLORS)], 1.6
            others += 1
        fig.add_trace(go.Scatter(
            x=result.series.index, y=result.series.to_numpy(),
            name=f"{result.label(lang)} ({result.return_pct:+.1f}%)",
            mode="lines",
            line=dict(color=color, width=width),
            opacity=1.0 if is_portfolio else 0.85,
            hovertemplate="%{fullData.name}<br>%{x|%d.%m.%Y}: %{y:.1f}<extra></extra>",
        ))
    baseline = "Başlangıç = 100" if lang == "tr" else "Start = 100"
    fig.add_hline(y=100, line_color="rgba(148,163,184,0.35)", line_width=1,
                  line_dash="dot", annotation_text=baseline,
                  annotation_font_color=_TEXT, annotation_font_size=10)
    fig.update_layout(
        legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top",
                    font=dict(size=10)),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def compare_bar(results: list[SeriesResult], lang: str) -> go.Figure:
    """Return ranking — the portfolio bar is highlighted."""
    ordered = sorted(results, key=lambda r: r.return_pct)
    colors = [
        _PORTFOLIO_COLOR if r.key == "portfolio"
        else (_GREEN if r.return_pct >= 0 else _RED)
        for r in ordered
    ]
    fig = go.Figure(go.Bar(
        x=[round(r.return_pct, 2) for r in ordered],
        y=[r.label(lang) for r in ordered],
        orientation="h", marker_color=colors,
        text=[f"{r.return_pct:+.1f}%" for r in ordered],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _base_layout(fig, height=max(260, 38 * len(ordered) + 80))


def allocation_with_cash_donut(
    metrics: list[PositionMetrics], cash_usd: float, cash_label: str
) -> go.Figure:
    """Allocation donut including a cash slice when there is cash."""
    labels = [m.symbol for m in metrics]
    values = [round(m.value_usd, 2) for m in metrics]
    colors = _PIE_COLORS[: len(metrics)] or list(_PIE_COLORS)
    if cash_usd > 0:
        labels.append(cash_label)
        values.append(round(cash_usd, 2))
        colors = [*colors, "#64748b"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent", textfont=dict(size=11),
        hovertemplate="%{label}: $%{value:,.0f} (%{percent})<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return _base_layout(fig, height=330)


def sentiment_gauge(score: float, label_text: str) -> go.Figure:
    """0–100 fear/greed dial: red (fear) on the left, green (greed) on the right."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score),
        title={"text": label_text, "font": {"size": 16, "color": _TEXT}},
        number={"font": {"size": 40, "color": _TEXT}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": _TEXT,
                     "tickfont": {"color": _TEXT, "size": 10}},
            "bar": {"color": _ACCENT, "thickness": 0.28},
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(248,113,113,0.55)"},
                {"range": [25, 45], "color": "rgba(251,146,60,0.45)"},
                {"range": [45, 55], "color": "rgba(148,163,184,0.35)"},
                {"range": [55, 75], "color": "rgba(163,230,53,0.40)"},
                {"range": [75, 100], "color": "rgba(52,211,153,0.55)"},
            ],
        },
    ))
    fig.update_layout(paper_bgcolor=_BG, font=dict(color=_TEXT),
                      height=280, margin=dict(l=30, r=30, t=60, b=10))
    return fig


def breadth_history(pct_50: pd.Series, pct_200: pd.Series, lang: str) -> go.Figure:
    """Participation over time: % of sample stocks above their 50/200-day MA."""
    label_50 = "SMA50 üstü %" if lang == "tr" else "% above SMA50"
    label_200 = "SMA200 üstü %" if lang == "tr" else "% above SMA200"
    fig = _base_layout(go.Figure(), height=320)
    fig.add_trace(go.Scatter(
        x=pct_50.index, y=pct_50.to_numpy(), name=label_50, mode="lines",
        line=dict(color=_ACCENT, width=1.6),
        hovertemplate="%{x|%d.%m.%Y}: %{y:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=pct_200.index, y=pct_200.to_numpy(), name=label_200, mode="lines",
        line=dict(color=_GOLD, width=2.0),
        hovertemplate="%{x|%d.%m.%Y}: %{y:.0f}%<extra></extra>",
    ))
    fig.add_hline(y=50, line_color="rgba(148,163,184,0.4)", line_width=1, line_dash="dot")
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return fig


def options_volume_bar(activities: list[OptionActivity], lang: str) -> go.Figure:
    """Call vs put volume per underlying, busiest at the top."""
    ordered = list(reversed(activities))  # horizontal bars render bottom-up
    call_label = "Call Hacmi" if lang == "tr" else "Call Volume"
    put_label = "Put Hacmi" if lang == "tr" else "Put Volume"
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[a.symbol for a in ordered], x=[a.call_volume for a in ordered],
        name=call_label, orientation="h", marker_color=_GREEN,
        hovertemplate="%{y} call: %{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=[a.symbol for a in ordered], x=[a.put_volume for a in ordered],
        name=put_label, orientation="h", marker_color=_RED,
        hovertemplate="%{y} put: %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(barmode="stack", xaxis_title=None, yaxis_title=None)
    return _base_layout(fig, height=max(300, 30 * len(ordered) + 100))


def history_line(history: list[dict], lang: str) -> go.Figure:
    dates = [h["date"] for h in history]
    values = [h["value_try"] for h in history]
    label = "Değer (TRY)" if lang == "tr" else "Value (TRY)"
    fig = go.Figure(go.Scatter(
        x=dates, y=values, name=label, mode="lines+markers",
        line=dict(color=_ACCENT, width=2.2),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.10)",
        hovertemplate="%{x}: %{y:,.0f} ₺<extra></extra>",
    ))
    return _base_layout(fig, height=300)
