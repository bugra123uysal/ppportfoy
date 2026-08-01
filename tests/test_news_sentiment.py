from __future__ import annotations

from portfoy.news_sentiment import NEGATIVE, NEUTRAL, POSITIVE, classify, interpret


class TestClassify:
    def test_positive_english_keyword(self):
        assert classify("Company beats estimates and raises guidance") == POSITIVE

    def test_positive_turkish_keyword(self):
        assert classify("Şirket beklentileri aştı, hisse rekor kırdı") == POSITIVE

    def test_negative_english_keyword(self):
        assert classify("Stock plunges after lawsuit filed") == NEGATIVE

    def test_negative_turkish_keyword(self):
        assert classify("Hisse sert düşüş yaşadı, soruşturma açıldı") == NEGATIVE

    def test_no_keywords_is_neutral(self):
        assert classify("Company announces quarterly board meeting date") == NEUTRAL

    def test_mixed_keywords_favor_higher_count(self):
        title = "Beats estimates but warns of a lawsuit and probe, misses guidance"
        # 1 positive ("beats estimates") vs 3 negative ("lawsuit", "probe", "misses")
        assert classify(title) == NEGATIVE

    def test_equal_counts_are_neutral(self):
        title = "Company beats estimates while facing a lawsuit"
        assert classify(title) == NEUTRAL

    def test_case_insensitive(self):
        assert classify("STOCK SURGES ON STRONG DEMAND") == POSITIVE


class TestInterpret:
    def test_returns_sentiment_and_turkish_line_by_default(self):
        sentiment, line = interpret("Company beats estimates")
        assert sentiment == POSITIVE
        assert "olumlu" in line

    def test_returns_english_line_when_requested(self):
        sentiment, line = interpret("Company beats estimates", lang="en")
        assert sentiment == POSITIVE
        assert "positive" in line

    def test_unknown_lang_falls_back_to_turkish(self):
        _, line = interpret("Company beats estimates", lang="fr")
        assert "olumlu" in line

    def test_negative_line_mentions_pressure(self):
        _, line = interpret("Stock plunges after lawsuit filed", lang="en")
        assert "pressure" in line

    def test_neutral_line_present(self):
        sentiment, line = interpret("Company announces quarterly board meeting date")
        assert sentiment == NEUTRAL
        assert line
