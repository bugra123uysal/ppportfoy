import pytest

from portfoy.security import (
    ValidationError,
    escape_html,
    is_safe_url,
    normalize_symbol,
    sanitize_note,
    validate_price,
    validate_quantity,
)


class TestNormalizeSymbol:
    def test_uppercases_and_trims(self):
        assert normalize_symbol("  aapl ") == "AAPL"

    def test_accepts_bist_suffix(self):
        assert normalize_symbol("thyao.is") == "THYAO.IS"

    def test_accepts_index_and_fx_forms(self):
        assert normalize_symbol("^GSPC") == "^GSPC"
        assert normalize_symbol("TRY=X") == "TRY=X"
        assert normalize_symbol("BRK-B") == "BRK-B"

    def test_turkish_dotless_i_normalized(self):
        assert normalize_symbol("asels.ıs") == "ASELS.IS"

    @pytest.mark.parametrize(
        "bad", ["", "  ", "AAPL; DROP TABLE", "<script>", "A" * 20, "$AAPL", "TH YAO", None, 42]
    )
    def test_rejects_garbage(self, bad):
        with pytest.raises(ValidationError):
            normalize_symbol(bad)


class TestNumericValidation:
    def test_valid_quantity(self):
        assert validate_quantity("10.5") == 10.5

    @pytest.mark.parametrize("bad", [0, -1, 1e10, float("nan"), float("inf"), "abc", None])
    def test_rejects_bad_quantity(self, bad):
        with pytest.raises(ValidationError):
            validate_quantity(bad)

    @pytest.mark.parametrize("bad", [0, -0.5, 1e10, float("nan"), "x"])
    def test_rejects_bad_price(self, bad):
        with pytest.raises(ValidationError):
            validate_price(bad)


class TestSanitizeAndEscape:
    def test_strips_control_chars(self):
        assert sanitize_note("hello\x00\x1bworld") == "helloworld"

    def test_caps_length(self):
        assert len(sanitize_note("x" * 1000)) == 300

    def test_non_string_becomes_empty(self):
        assert sanitize_note(123) == ""

    def test_escape_html_blocks_injection(self):
        assert "<script>" not in escape_html('<script>alert("x")</script>')
        assert escape_html('a"b') == "a&quot;b"


class TestSafeUrl:
    def test_https_ok(self):
        assert is_safe_url("https://news.example.com/article?id=1")

    @pytest.mark.parametrize(
        "bad",
        ["javascript:alert(1)", "file:///etc/passwd", "ftp://x", "", None,
         "data:text/html,x", "https://" , "http://" + "a" * 3000],
    )
    def test_bad_schemes_rejected(self, bad):
        assert not is_safe_url(bad)
