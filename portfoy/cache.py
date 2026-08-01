"""Pluggable TTL cache, replacing Streamlit's ``st.cache_data`` outside a
Streamlit process.

Vercel Python functions are stateless between invocations, so an in-process
dict does not survive a cold start the way it does inside Streamlit's
long-running server. Upstash's Redis REST API does. The backend is picked
automatically: Upstash when ``UPSTASH_REDIS_REST_URL`` /
``UPSTASH_REDIS_REST_TOKEN`` are set (the historical naming) or, failing
that, ``KV_REST_API_URL`` / ``KV_REST_API_TOKEN`` (what the current Vercel
Marketplace "Upstash for Redis" integration actually provisions), otherwise
an in-process dict (correct for Streamlit, and for local dev/tests where no
Upstash project exists yet).

Caching is a performance optimization, never a correctness dependency: any
backend failure (network error, corrupt entry) is swallowed and the wrapped
function is simply called directly, exactly as on a cache miss.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

Encoder = Callable[[Any], str]
Decoder = Callable[[str], Any]

_UPSTASH_TIMEOUT = 3.0  # seconds; a slow cache must never stall the request


class CacheBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: int) -> None: ...


class InProcessBackend:
    """One dict per process. Lost on cold start -- fine for Streamlit, fine
    as the Upstash fallback, fine for tests."""

    def __init__(self, now: Callable[[], float] = time.time) -> None:
        self._now = now
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._now() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int) -> None:
        self._store[key] = (self._now() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


class UpstashBackend:
    """Upstash Redis REST API via stdlib ``urllib`` only -- deliberately no
    redis client dependency, since every extra package here counts against
    the Vercel Python function's 250MB unzipped size limit."""

    def __init__(self, url: str, token: str, timeout: float = _UPSTASH_TIMEOUT) -> None:
        self._url = url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def get(self, key: str) -> str | None:
        request = urllib.request.Request(  # noqa: S310 -- self._url is our own configured endpoint, not user input
            f"{self._url}/get/{urllib.parse.quote(key, safe='')}",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            body = json.loads(response.read())
        result = body.get("result")
        return result if isinstance(result, str) else None

    def set(self, key: str, value: str, ttl: int) -> None:
        quoted_key = urllib.parse.quote(key, safe="")
        quoted_value = urllib.parse.quote(value, safe="")
        path = f"{self._url}/set/{quoted_key}/{quoted_value}"
        request = urllib.request.Request(  # noqa: S310 -- self._url is our own configured endpoint, not user input
            f"{path}?EX={int(ttl)}",
            headers={"Authorization": f"Bearer {self._token}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout):  # noqa: S310
            pass


_backend: CacheBackend | None = None


def get_backend() -> CacheBackend:
    """The process-wide cache backend, selected once and reused."""
    global _backend
    if _backend is not None:
        return _backend
    url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip() or os.environ.get(
        "KV_REST_API_URL", ""
    ).strip()
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip() or os.environ.get(
        "KV_REST_API_TOKEN", ""
    ).strip()
    _backend = UpstashBackend(url, token) if url and token else InProcessBackend()
    return _backend


def set_backend(backend: CacheBackend | None) -> None:
    """Override the backend (tests), or pass None to force re-selection from env."""
    global _backend
    _backend = backend


def clear_all() -> None:
    """Best-effort cache wipe for the manual refresh button.

    A no-op for backends that don't support clearing (e.g. Upstash, where
    entries simply expire on their own TTL) -- refreshing must never be the
    reason a page fails to load.
    """
    clear = getattr(get_backend(), "clear", None)
    if callable(clear):
        clear()


def cached(ttl: int, *, encode: Encoder = json.dumps, decode: Decoder = json.loads) -> Callable:
    """Cache a function's return value for ``ttl`` seconds.

    ``encode``/``decode`` default to plain JSON, which covers everything
    already JSON-safe (use ``portfoy.serialize.dumps`` / a custom decoder for
    dataclasses, NamedTuples, or pandas objects that need to survive the
    round trip as their original type).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            backend = get_backend()
            key = _make_key(fn, args, kwargs)
            raw = _safe_get(backend, key)
            if raw is not None:
                try:
                    return decode(raw)
                except (ValueError, TypeError, KeyError):
                    pass  # corrupt/incompatible entry -- recompute below
            result = fn(*args, **kwargs)
            _safe_set(backend, key, result, ttl, encode)
            return result

        return wrapper

    return decorator


def _make_key(fn: Callable, args: tuple, kwargs: dict) -> str:
    raw = json.dumps(
        {"fn": f"{fn.__module__}.{fn.__qualname__}", "args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"portfoy:{fn.__qualname__}:{digest}"


def _safe_get(backend: CacheBackend, key: str) -> str | None:
    try:
        return backend.get(key)
    except Exception:
        # A cache read must never be the reason a page fails to load.
        return None


def _safe_set(backend: CacheBackend, key: str, result: Any, ttl: int, encode: Encoder) -> None:
    try:
        backend.set(key, encode(result), ttl)
    except Exception:  # noqa: S110 -- caching is best-effort only, see module docstring
        pass
