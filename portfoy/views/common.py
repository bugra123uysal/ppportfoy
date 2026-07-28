"""Shared UI building blocks: CSS, cards, macro strip, formatting.

Any dynamic value embedded in HTML goes through escape_html() first.
"""

from __future__ import annotations

import streamlit as st

from ..i18n import t
from ..security import escape_html

_CSS = """
<style>
:root {
  --bg: #0b1120; --card: #111a2e; --card2: #16213a;
  --border: rgba(148,163,184,0.14); --text: #e2e8f0; --muted: #94a3b8;
  --green: #34d399; --red: #f87171; --accent: #818cf8; --gold: #fbbf24;
}
.stApp { background: radial-gradient(1200px 600px at 15% -10%, #1e1b4b33, transparent), var(--bg); }
section[data-testid="stSidebar"] { background: #0d1526; border-right: 1px solid var(--border); }
h1, h2, h3 { color: var(--text) !important; letter-spacing: -0.02em; }

.hero {
  padding: 1.1rem 1.4rem; border-radius: 16px; margin-bottom: 1rem;
  background: linear-gradient(120deg, #1e1b4b 0%, #111a2e 55%, #0b1120 100%);
  border: 1px solid var(--border);
}
.hero .title { font-size: 1.55rem; font-weight: 700; color: var(--text); }
.hero .sub { color: var(--muted); font-size: 0.9rem; margin-top: 0.15rem; }

.metric-card {
  background: linear-gradient(160deg, var(--card2), var(--card));
  border: 1px solid var(--border); border-radius: 14px;
  padding: 0.9rem 1.05rem; height: 100%;
}
.metric-card .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
.metric-card .value { color: var(--text); font-size: 1.45rem; font-weight: 700; margin-top: 0.15rem; }
.metric-card .delta { font-size: 0.86rem; font-weight: 600; margin-top: 0.1rem; }
.up { color: var(--green); } .down { color: var(--red); } .flat { color: var(--muted); }

.macro-strip { display: flex; gap: 0.55rem; overflow-x: auto; padding-bottom: 0.35rem; }
.macro-chip {
  min-width: 118px; flex: 0 0 auto; background: var(--card);
  border: 1px solid var(--border); border-radius: 12px; padding: 0.55rem 0.75rem;
}
.macro-chip .m-label { color: var(--muted); font-size: 0.72rem; }
.macro-chip .m-price { color: var(--text); font-size: 0.95rem; font-weight: 600; }
.macro-chip .m-chg { font-size: 0.78rem; font-weight: 600; }

.alert-card {
  border-radius: 12px; padding: 0.7rem 0.95rem; margin-bottom: 0.5rem;
  background: var(--card); border: 1px solid var(--border);
  border-left: 4px solid var(--muted); color: var(--text); font-size: 0.92rem;
}
.alert-crit { border-left-color: var(--red); background: linear-gradient(90deg, rgba(248,113,113,0.10), var(--card)); }
.alert-warn { border-left-color: var(--gold); background: linear-gradient(90deg, rgba(251,191,36,0.08), var(--card)); }
.alert-info { border-left-color: var(--accent); }
.badge {
  display: inline-block; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
  padding: 0.12rem 0.5rem; border-radius: 999px; margin-right: 0.5rem; vertical-align: 1px;
}
.badge-crit { background: rgba(248,113,113,0.18); color: var(--red); }
.badge-warn { background: rgba(251,191,36,0.16); color: var(--gold); }
.badge-info { background: rgba(129,140,248,0.18); color: var(--accent); }

.news-card {
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  padding: 0.8rem 1rem; margin-bottom: 0.55rem;
}
.news-card a { color: var(--text); text-decoration: none; font-weight: 600; font-size: 0.95rem; }
.news-card a:hover { color: var(--accent); }
.news-meta { color: var(--muted); font-size: 0.76rem; margin-top: 0.25rem; }
.news-sym {
  background: rgba(129,140,248,0.16); color: var(--accent); border-radius: 6px;
  padding: 0.05rem 0.45rem; font-size: 0.72rem; font-weight: 700; margin-right: 0.45rem;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="title">{escape_html(title)}</div>'
        f'<div class="sub">{escape_html(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, delta: float | None = None, suffix: str = "%") -> str:
    delta_html = ""
    if delta is not None:
        cls = "up" if delta > 0 else "down" if delta < 0 else "flat"
        arrow = "▲" if delta > 0 else "▼" if delta < 0 else "•"
        delta_html = f'<div class="delta {cls}">{arrow} {abs(delta):.2f}{escape_html(suffix)}</div>'
    return (
        f'<div class="metric-card"><div class="label">{escape_html(label)}</div>'
        f'<div class="value">{escape_html(value)}</div>{delta_html}</div>'
    )


def macro_strip(snapshot: list[dict]) -> None:
    chips = []
    for row in snapshot:
        chg = float(row["change_pct"])
        cls = "up" if chg > 0 else "down" if chg < 0 else "flat"
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else "•"
        price = f"{row['price']:,.2f}" if row["price"] < 10000 else f"{row['price']:,.0f}"
        chips.append(
            f'<div class="macro-chip"><div class="m-label">{escape_html(row["label"])}</div>'
            f'<div class="m-price">{escape_html(price)}</div>'
            f'<div class="m-chg {cls}">{arrow} {abs(chg):.2f}%</div></div>'
        )
    st.markdown(f'<div class="macro-strip">{"".join(chips)}</div>', unsafe_allow_html=True)


def alert_card(alert, lang: str) -> None:
    text = t(alert.key, lang, **alert.params)
    badge = t(f"severity_{alert.severity}", lang)
    st.markdown(
        f'<div class="alert-card alert-{alert.severity}">'
        f'<span class="badge badge-{alert.severity}">{escape_html(badge)}</span>'
        f"{escape_html(text)}</div>",
        unsafe_allow_html=True,
    )


def fmt_money(value: float, currency: str) -> str:
    symbol = "₺" if currency == "TRY" else "$"
    return f"{symbol}{value:,.2f}" if abs(value) < 100000 else f"{symbol}{value:,.0f}"
