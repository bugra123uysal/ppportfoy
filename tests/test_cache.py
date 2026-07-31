from __future__ import annotations

import pytest

from portfoy.cache import InProcessBackend, UpstashBackend, cached, get_backend, set_backend


class FakeClock:
    """Deterministic stand-in for time.time(), so TTL tests don't sleep."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def isolated_backend():
    """Every test gets its own in-process backend so state can't bleed across tests."""
    set_backend(InProcessBackend())
    yield
    set_backend(None)


class TestTtlExpiry:
    def test_cached_result_reused_before_ttl(self):
        calls = []

        @cached(ttl=60)
        def fn(x):
            calls.append(x)
            return x * 2

        assert fn(3) == 6
        assert fn(3) == 6
        assert calls == [3]  # second call served from cache, fn not re-entered

    def test_recomputes_after_ttl_expires(self):
        clock = FakeClock()
        set_backend(InProcessBackend(now=clock))
        calls = []

        @cached(ttl=10)
        def fn(x):
            calls.append(x)
            return x * 2

        assert fn(3) == 6
        clock.advance(11)
        assert fn(3) == 6
        assert calls == [3, 3]

    def test_still_cached_just_before_ttl_expires(self):
        clock = FakeClock()
        set_backend(InProcessBackend(now=clock))
        calls = []

        @cached(ttl=10)
        def fn(x):
            calls.append(x)
            return x * 2

        fn(3)
        clock.advance(9)
        fn(3)
        assert calls == [3]


class TestKeyDerivation:
    def test_different_args_do_not_share_a_cache_entry(self):
        calls = []

        @cached(ttl=60)
        def fn(x):
            calls.append(x)
            return x

        fn(1)
        fn(2)
        assert calls == [1, 2]

    def test_kwargs_are_part_of_the_key(self):
        calls = []

        @cached(ttl=60)
        def fn(x, *, mode="a"):
            calls.append((x, mode))
            return mode

        fn(1, mode="a")
        fn(1, mode="b")
        assert calls == [(1, "a"), (1, "b")]

    def test_two_functions_do_not_collide_on_the_same_args(self):
        calls_a, calls_b = [], []

        @cached(ttl=60)
        def fn_a(x):
            calls_a.append(x)
            return "a"

        @cached(ttl=60)
        def fn_b(x):
            calls_b.append(x)
            return "b"

        fn_a(1)
        fn_b(1)
        assert calls_a == [1]
        assert calls_b == [1]


class TestBackendFallback:
    def test_get_failure_degrades_to_calling_the_function(self):
        class BrokenBackend:
            def get(self, key):
                raise ConnectionError("unreachable")

            def set(self, key, value, ttl):
                raise ConnectionError("unreachable")

        set_backend(BrokenBackend())

        @cached(ttl=60)
        def fn(x):
            return x * 2

        assert fn(3) == 6

    def test_corrupt_cache_entry_falls_back_to_recompute(self):
        class GarbageBackend:
            def get(self, key):
                return "{not valid json"

            def set(self, key, value, ttl):
                pass

        set_backend(GarbageBackend())

        @cached(ttl=60)
        def fn(x):
            return x * 2

        assert fn(3) == 6


class TestBackendSelection:
    def test_defaults_to_in_process_without_upstash_env(self, monkeypatch):
        monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
        monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
        set_backend(None)
        assert isinstance(get_backend(), InProcessBackend)

    def test_selects_upstash_when_env_configured(self, monkeypatch):
        monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
        monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "secret-token")
        set_backend(None)
        assert isinstance(get_backend(), UpstashBackend)

    def test_missing_token_alone_does_not_select_upstash(self, monkeypatch):
        monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
        monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
        set_backend(None)
        assert isinstance(get_backend(), InProcessBackend)


class TestCustomCodec:
    def test_custom_encode_decode_used(self):
        @cached(
            ttl=60,
            encode=lambda v: f"wrapped:{v}",
            decode=lambda s: s.removeprefix("wrapped:"),
        )
        def fn(x):
            return str(x)

        assert fn(1) == "1"
        assert fn(1) == "1"
