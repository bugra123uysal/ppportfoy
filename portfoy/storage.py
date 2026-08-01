"""Persistent portfolio storage.

Positions and cash live in a local JSON file. Writes are atomic (tmp file +
os.replace) so a crash mid-write can never corrupt the portfolio.
All mutation helpers are pure: they return new lists instead of
modifying their inputs.

The file holds ``{"positions": [...], "cash": [...]}``. A bare list — the
format used before cash existed — is still read as a positions-only file.

Demo mode (``PORTFOY_DEMO=1``): for public deployments nothing touches the
disk. Each visitor gets an isolated, session-only copy seeded with an example
portfolio, so a shared instance never exposes or mixes anyone's data and
ephemeral cloud filesystems stop mattering.

Serverless fallback (``PORTFOY_PORTFOLIO_JSON`` / ``PORTFOY_HISTORY_JSON``):
``data/`` is gitignored, so a platform that deploys from git (Vercel) never
has the on-disk file to read. When the file is missing, these env vars --
holding the same JSON the file would -- are read instead, seeding the very
first read before anything has been written to persistent storage.

Persistent storage on Vercel (Upstash, via ``cache.get_persistent_backend()``):
Vercel's function filesystem is read-only outside ``/tmp``, and ``/tmp``
itself isn't kept between invocations, so writes (adding/removing a
position from the web app) cannot go to a local file there. When Upstash is
configured, reads and writes both go through it instead of the local file --
Upstash always wins over the env-var seed once something has actually been
written, since it reflects the current mutable state. Local/Streamlit use is
unaffected: Upstash env vars are never set in that environment, so this
module falls straight back to plain file I/O, unchanged.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path

from . import cache, config
from .security import (
    ValidationError,
    normalize_symbol,
    sanitize_note,
    validate_cash,
    validate_currency,
    validate_price,
    validate_quantity,
)


@dataclass(frozen=True)
class CashHolding:
    currency: str             # "TRY" or "USD"
    amount: float


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    avg_cost: float           # in the position's own currency
    currency: str             # "TRY" or "USD" (derived from symbol suffix)
    added: str                # ISO date
    notes: str = ""


def currency_for(symbol: str) -> str:
    return "TRY" if symbol.endswith(".IS") else "USD"


def make_position(symbol: str, quantity: float, avg_cost: float, notes: str = "") -> Position:
    """Validate raw form input and build a Position."""
    sym = normalize_symbol(symbol)
    return Position(
        symbol=sym,
        quantity=validate_quantity(quantity),
        avg_cost=validate_price(avg_cost),
        currency=currency_for(sym),
        added=date.today().isoformat(),
        notes=sanitize_note(notes),
    )


def make_cash(currency: str, amount: float) -> CashHolding:
    """Validate raw form input and build a CashHolding."""
    return CashHolding(currency=validate_currency(currency), amount=validate_cash(amount))


# --- load / save -----------------------------------------------------------

def load_portfolio(path: Path = config.PORTFOLIO_FILE) -> list[Position]:
    """Load positions, silently skipping any entry that fails validation."""
    raw = _positions_payload(_read_json(path))
    positions: list[Position] = []
    for item in raw[: config.MAX_POSITIONS]:
        try:
            positions.append(
                Position(
                    symbol=normalize_symbol(item["symbol"]),
                    quantity=validate_quantity(item["quantity"]),
                    avg_cost=validate_price(item["avg_cost"]),
                    currency="TRY" if item.get("currency") == "TRY" else "USD",
                    added=str(item.get("added", ""))[:10],
                    notes=sanitize_note(item.get("notes", "")),
                )
            )
        except (ValidationError, KeyError, TypeError):
            continue
    return positions


def load_cash(path: Path = config.PORTFOLIO_FILE) -> list[CashHolding]:
    """Load cash balances, one entry per currency, skipping invalid rows."""
    raw = _read_json(path)
    if not isinstance(raw, dict):
        return []
    entries = raw.get("cash")
    if not isinstance(entries, list):
        return []
    holdings: dict[str, CashHolding] = {}
    for item in entries:
        try:
            holding = make_cash(item["currency"], item["amount"])
        except (ValidationError, KeyError, TypeError):
            continue
        holdings[holding.currency] = holding
    return list(holdings.values())


def save_portfolio(
    positions: list[Position],
    path: Path = config.PORTFOLIO_FILE,
    cash: list[CashHolding] | None = None,
) -> None:
    """Persist positions. Cash is left untouched unless explicitly supplied."""
    balances = load_cash(path) if cash is None else cash
    _write_json_atomic(
        path,
        {
            "positions": [asdict(p) for p in positions[: config.MAX_POSITIONS]],
            "cash": [asdict(c) for c in balances],
        },
    )


def save_cash(cash: list[CashHolding], path: Path = config.PORTFOLIO_FILE) -> None:
    """Persist cash balances, leaving positions untouched."""
    save_portfolio(load_portfolio(path), path, cash=cash)


def set_cash(cash: list[CashHolding], currency: str, amount: float) -> list[CashHolding]:
    """Set one currency's balance. Zero removes the entry. Returns a new list."""
    target = validate_currency(currency)
    kept = [c for c in cash if c.currency != target]
    if validate_cash(amount) <= 0:
        return kept
    return [*kept, make_cash(target, amount)]


# --- pure mutations --------------------------------------------------------

def upsert_position(positions: list[Position], new: Position) -> list[Position]:
    """Add a position; if the symbol exists, merge into a weighted average cost."""
    for i, existing in enumerate(positions):
        if existing.symbol == new.symbol:
            total_qty = existing.quantity + new.quantity
            merged_cost = (
                existing.quantity * existing.avg_cost + new.quantity * new.avg_cost
            ) / total_qty
            merged = replace(
                existing,
                quantity=total_qty,
                avg_cost=round(merged_cost, 6),
                notes=new.notes or existing.notes,
            )
            return [*positions[:i], merged, *positions[i + 1:]]
    if len(positions) >= config.MAX_POSITIONS:
        raise ValidationError(f"En fazla {config.MAX_POSITIONS} pozisyon eklenebilir")
    return [*positions, new]


def remove_position(positions: list[Position], symbol: str) -> list[Position]:
    return [p for p in positions if p.symbol != symbol]


def reduce_position(positions: list[Position], symbol: str, quantity: float) -> list[Position]:
    """Sell some (or all) of a position. Removes it when quantity reaches zero."""
    qty = validate_quantity(quantity)
    result: list[Position] = []
    for p in positions:
        if p.symbol != symbol:
            result.append(p)
        elif p.quantity - qty > 1e-9:
            result.append(replace(p, quantity=p.quantity - qty))
    return result


# --- daily value snapshots (for the portfolio history chart) ---------------

def load_history(path: Path = config.HISTORY_FILE) -> list[dict]:
    raw = _read_json(path)
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw[-config.MAX_HISTORY_DAYS:]:
        try:
            out.append(
                {
                    "date": str(item["date"])[:10],
                    "value_try": float(item["value_try"]),
                    "value_usd": float(item["value_usd"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out


def append_snapshot(
    value_try: float, value_usd: float, path: Path = config.HISTORY_FILE
) -> list[dict]:
    """Record today's portfolio value (one entry per day, last write wins)."""
    today = datetime.now(UTC).date().isoformat()
    history = [h for h in load_history(path) if h["date"] != today]
    history.append(
        {"date": today, "value_try": round(value_try, 2), "value_usd": round(value_usd, 2)}
    )
    history = history[-config.MAX_HISTORY_DAYS:]
    _write_json_atomic(path, history)
    return history


# --- demo mode (public deployments) ----------------------------------------

DEMO_SEED: dict = {
    "positions": [
        {"symbol": "NVDA", "quantity": 12.0, "avg_cost": 168.0,
         "currency": "USD", "added": "2026-05-04", "notes": ""},
        {"symbol": "AAPL", "quantity": 10.0, "avg_cost": 310.0,
         "currency": "USD", "added": "2026-04-13", "notes": ""},
        {"symbol": "MSFT", "quantity": 6.0, "avg_cost": 405.0,
         "currency": "USD", "added": "2026-06-01", "notes": ""},
        {"symbol": "THYAO.IS", "quantity": 150.0, "avg_cost": 285.0,
         "currency": "TRY", "added": "2026-03-20", "notes": ""},
        {"symbol": "ASELS.IS", "quantity": 80.0, "avg_cost": 372.0,
         "currency": "TRY", "added": "2026-06-15", "notes": ""},
    ],
    "cash": [
        {"currency": "USD", "amount": 1500.0},
        {"currency": "TRY", "amount": 25000.0},
    ],
}


def is_demo() -> bool:
    """True when the app runs as a public demo (set PORTFOY_DEMO=1)."""
    return os.environ.get("PORTFOY_DEMO", "").strip().lower() in {"1", "true", "yes"}


def _session_store() -> dict | None:
    """Per-visitor in-memory file store, or None when disk storage applies.

    Only active in demo mode inside a running Streamlit server; tests and
    bare scripts fall through to the regular disk path.
    """
    if not is_demo():
        return None
    try:
        import streamlit as st
        from streamlit import runtime
    except ImportError:
        return None
    if not runtime.exists():
        return None
    if "_demo_files" not in st.session_state:
        st.session_state["_demo_files"] = {
            str(config.PORTFOLIO_FILE): copy.deepcopy(DEMO_SEED),
        }
    return st.session_state["_demo_files"]


# --- low-level JSON helpers ------------------------------------------------

def _positions_payload(raw: object) -> list:
    """Positions from either the current dict format or the legacy bare list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        entries = raw.get("positions")
        return entries if isinstance(entries, list) else []
    return []


_ENV_FALLBACKS = {
    config.PORTFOLIO_FILE: "PORTFOY_PORTFOLIO_JSON",
    config.HISTORY_FILE: "PORTFOY_HISTORY_JSON",
}

_PERSISTENT_KEYS = {
    config.PORTFOLIO_FILE: "portfoy:storage:portfolio",
    config.HISTORY_FILE: "portfoy:storage:history",
}


def can_persist() -> bool:
    """True when a write made right now will actually survive.

    Local/Streamlit use always has a writable working directory, so this is
    only False in the one case that matters: running on Vercel (a read-only
    filesystem outside /tmp, which itself isn't kept between invocations)
    without Upstash configured to take writes instead. Callers that mutate
    storage (e.g. the API's add/remove-position routes) should check this
    first and fail with a clear error rather than let an unwritable-
    filesystem OSError surface as a generic 500.
    """
    if is_demo():
        return True
    if cache.get_persistent_backend() is not None:
        return True
    return os.environ.get("VERCEL", "").strip() != "1"


def _read_json(path: Path) -> object:
    store = _session_store()
    if store is not None:
        return store.get(str(path))
    persistent = _persistent_value(path)
    if persistent is not None:
        return persistent
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return _env_fallback(path)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _persistent_value(path: Path) -> object:
    key = _PERSISTENT_KEYS.get(path)
    if key is None:
        return None
    backend = cache.get_persistent_backend()
    if backend is None:
        return None
    try:
        raw = backend.get(key)
    except Exception:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _env_fallback(path: Path) -> object:
    var = _ENV_FALLBACKS.get(path)
    if var is None:
        return None
    raw = os.environ.get(var, "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _write_json_atomic(path: Path, payload: object) -> None:
    store = _session_store()
    if store is not None:
        store[str(path)] = payload
        return
    key = _PERSISTENT_KEYS.get(path)
    if key is not None:
        backend = cache.get_persistent_backend()
        if backend is not None:
            backend.set_forever(key, json.dumps(payload, ensure_ascii=False))
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
