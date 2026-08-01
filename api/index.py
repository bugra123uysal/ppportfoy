"""Vercel entrypoint: read-only JSON API over the portfolio's computed data.

GET-only by design: Vercel's filesystem is read-only at request time (only
/tmp is writable, and it isn't persisted between invocations), so mutating
endpoints (add/remove a position) stay a Streamlit-only feature -- see
portfoy.storage's module docstring.

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

from portfoy import api_data, config  # noqa: E402
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


@app.get("/api/positions")
def positions() -> Response:
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


@app.get("/api/calendar")
def calendar() -> Response:
    days = request.args.get("days", type=int) or config.CALENDAR_LOOKAHEAD_DAYS
    days = max(1, min(days, 365))
    return _json_response(api_data.calendar_payload(days))


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
