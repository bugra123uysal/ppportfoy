from __future__ import annotations

from datetime import UTC, datetime

import pytest

from portfoy import news
from portfoy.cache import InProcessBackend, set_backend


@pytest.fixture(autouse=True)
def isolated_cache():
    """get_news_for is @cached -- give every test a fresh backend so results
    from one test don't leak into the next via the shared process cache."""
    set_backend(InProcessBackend())
    yield
    set_backend(None)


def _item(title: str, published=None) -> dict:
    return {
        "symbol": "AAPL",
        "title": title,
        "link": "https://example.com/a",
        "source": "Test Source",
        "published": published or datetime(2026, 1, 1, tzinfo=UTC),
    }


class TestGetNewsForTagsSentiment:
    def test_items_are_tagged_with_sentiment_and_interpretation(self, monkeypatch):
        monkeypatch.setattr(news, "_yahoo_news", lambda sym: [_item("Company beats estimates")])
        monkeypatch.setattr(news, "_google_news", lambda sym, lang: [])
        out = news.get_news_for("AAPL", "en")
        assert out[0]["sentiment"] == "positive"
        assert "positive" in out[0]["interpretation"]

    def test_interpretation_language_follows_lang_argument(self, monkeypatch):
        monkeypatch.setattr(news, "_yahoo_news", lambda sym: [_item("Company beats estimates")])
        monkeypatch.setattr(news, "_google_news", lambda sym, lang: [])
        out = news.get_news_for("AAPL", "tr")
        assert "olumlu" in out[0]["interpretation"]

    def test_deduplicated_items_still_tagged(self, monkeypatch):
        monkeypatch.setattr(
            news, "_yahoo_news",
            lambda sym: [_item("Stock plunges after lawsuit filed")],
        )
        monkeypatch.setattr(news, "_google_news", lambda sym, lang: [])
        out = news.get_news_for("AAPL", "en")
        assert len(out) == 1
        assert out[0]["sentiment"] == "negative"
