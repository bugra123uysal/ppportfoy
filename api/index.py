"""Vercel entrypoint: JSON API over the portfolio's computed data.

Mostly read-only: Vercel's filesystem is read-only at request time (only
/tmp is writable, and it isn't persisted between invocations), so mutating
endpoints (add/remove a position) only work when a persistent backend is
configured (Upstash -- see portfoy.storage's module docstring and
storage.can_persist()). They fail with a clear 503 rather than a
generic-looking write that silently doesn't survive the next cold start.

This service (see vercel.json's `services.api`) has no public rewrite of its
own -- the "web" Next.js service reaches it only through an internal service
binding (PORTFOY_API_URL), never over the public internet. The PORTFOY_API_KEY
check below is defense-in-depth on top of that (a binding grants network
reachability, not authorization -- see the Vercel service-bindings docs), and
is what protects this data if the API is ever exposed by mistake.
"""

from __future__ import annotations

import hmac
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, Response, request  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from portfoy import api_data, config, storage  # noqa: E402
from portfoy import movers as movers_module  # noqa: E402
from portfoy.security import ValidationError, normalize_symbol  # noqa: E402
from portfoy.serialize import dumps  # noqa: E402

app = Flask(__name__)

_LANGS = ("tr", "en")


def _json_response(payload: object, status: int = 200) -> Response:
    return Response(dumps(payload), status=status, mimetype="application/json")


def _authorized() -> bool:
    expected = os.environ.get("PORTFOY_API_KEY", "").strip()
    if not expected:
        return False  # no key configured -- fail closed, never serve unauthenticated
    # Header only, deliberately -- a query-string fallback would let the key
    # leak into access/proxy logs and browser history for no benefit (the
    # only caller, web/src/lib/api.ts, always sends the header).
    supplied = request.headers.get("X-API-Key") or ""
    return hmac.compare_digest(supplied, expected)


@app.before_request
def _require_api_key() -> Response | None:
    if not _authorized():
        return _json_response({"error": "unauthorized"}, status=401)
    return None


@app.errorhandler(HTTPException)
def _http_error(err: HTTPException) -> Response:
    return _json_response({"error": err.name.lower().replace(" ", "_")}, status=err.code or 500)


@app.errorhandler(Exception)
def _unhandled_error(err: Exception) -> Response:
    app.logger.exception("Unhandled API error: %s", err)
    return _json_response({"error": "internal_error"}, status=500)


def _clean_symbol(raw: str) -> str:
    try:
        return normalize_symbol(raw)
    except ValidationError as exc:
        raise _bad_request(str(exc)) from exc


def _bad_request(message: str) -> HTTPException:
    from werkzeug.exceptions import BadRequest

    return BadRequest(message)


def _require_persistence() -> Response | None:
    if storage.can_persist():
        return None
    return _json_response({"error": "storage_not_configured"}, status=503)


@app.get("/api/positions")
def positions() -> Response:
    return _json_response(api_data.positions_payload())


@app.post("/api/positions")
def add_position() -> Response:
    unavailable = _require_persistence()
    if unavailable is not None:
        return unavailable
    body = request.get_json(silent=True) or {}
    try:
        new_position = storage.make_position(
            body.get("symbol", ""),
            body.get("quantity"),
            body.get("avg_cost"),
            body.get("notes", ""),
        )
        updated = storage.upsert_position(storage.load_portfolio(), new_position)
    except ValidationError as exc:
        raise _bad_request(str(exc)) from exc
    storage.save_portfolio(updated)
    return _json_response(api_data.positions_payload())


@app.delete("/api/positions/<symbol>")
def delete_position(symbol: str) -> Response:
    unavailable = _require_persistence()
    if unavailable is not None:
        return unavailable
    clean = _clean_symbol(symbol)
    updated = storage.remove_position(storage.load_portfolio(), clean)
    storage.save_portfolio(updated)
    return _json_response(api_data.positions_payload())


@app.get("/api/portfolio/summary")
def portfolio_summary() -> Response:
    return _json_response(api_data.portfolio_summary_payload())


@app.get("/api/portfolio/history")
def portfolio_history() -> Response:
    return _json_response(api_data.portfolio_history_payload())


@app.get("/api/rotation")
def rotation() -> Response:
    include_mine = request.args.get("include_mine", "").strip().lower() in ("1", "true", "yes")
    return _json_response(api_data.rotation_payload(include_mine))


@app.get("/api/trade-scan")
def trade_scan() -> Response:
    return _json_response(api_data.trade_scan_payload())


@app.get("/api/money-flow")
def money_flow() -> Response:
    return _json_response(api_data.money_flow_payload())


@app.get("/api/fundamentals")
def fundamentals() -> Response:
    return _json_response(api_data.fundamental_scan_payload())


@app.get("/api/vcp-scan")
def vcp_scan() -> Response:
    return _json_response(api_data.vcp_scan_payload())


@app.get("/api/options")
def options_scan() -> Response:
    return _json_response(api_data.options_scan_payload())


@app.get("/api/options/<symbol>")
def option_activity(symbol: str) -> Response:
    return _json_response(api_data.option_activity_payload(_clean_symbol(symbol)))


@app.get("/api/market/breadth")
def market_breadth() -> Response:
    return _json_response(api_data.breadth_payload())


@app.get("/api/market/sentiment")
def market_sentiment() -> Response:
    return _json_response(api_data.sentiment_payload())


@app.get("/api/market/macro")
def market_macro() -> Response:
    return _json_response(api_data.macro_payload())


@app.get("/api/market/yield-curve")
def market_yield_curve() -> Response:
    return _json_response(api_data.yield_curve_payload())


@app.get("/api/analyst")
def analyst() -> Response:
    return _json_response(api_data.analyst_payload())


@app.get("/api/calendar")
def calendar() -> Response:
    days = request.args.get("days", type=int) or config.CALENDAR_LOOKAHEAD_DAYS
    days = max(1, min(days, 365))
    return _json_response(api_data.calendar_payload(days))


@app.get("/api/movers")
def movers() -> Response:
    return _json_response(api_data.movers_payload())


@app.post("/api/movers/scan")
def movers_scan() -> Response:
    """Runs the (slow) live scan and persists it, unless the last snapshot is
    still fresh (scan_if_due's own min-interval backstop) -- meant to be
    triggered by an external scheduler (see
    web/src/app/api/cron/movers-scan/route.ts), not by the page. Behind the
    same PORTFOY_API_KEY gate as every other route here; the internal
    service binding is the only way to reach it."""
    return _json_response(movers_module.scan_if_due())


@app.get("/api/news/<symbol>")
def news(symbol: str) -> Response:
    lang = request.args.get("lang", "tr").strip().lower()
    if lang not in _LANGS:
        lang = "tr"
    return _json_response(api_data.news_payload(_clean_symbol(symbol), lang))


@app.get("/api/compare")
def compare() -> Response:
    period = request.args.get("period", config.DEFAULT_COMPARE_PERIOD)
    if period not in config.COMPARE_PERIODS:
        raise _bad_request(f"unknown period: {period!r}")
    base = request.args.get("base", "USD").strip().upper()
    if base not in config.CASH_CURRENCIES:
        raise _bad_request(f"unknown base currency: {base!r}")
    return _json_response(api_data.compare_payload(period, base))
