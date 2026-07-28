import json

import pytest

from portfoy.data import Quote
from portfoy.risk import cash_totals, compute_metrics, portfolio_totals
from portfoy.security import ValidationError, validate_cash, validate_currency
from portfoy.storage import (
    CashHolding,
    load_cash,
    load_portfolio,
    make_cash,
    make_position,
    save_cash,
    save_portfolio,
    set_cash,
)


@pytest.fixture
def path(tmp_path):
    return tmp_path / "portfolio.json"


class TestCashValidation:
    def test_zero_allowed(self):
        assert validate_cash(0) == 0.0

    @pytest.mark.parametrize("bad", [-1, 1e13, float("nan"), float("inf"), "abc", None])
    def test_rejects_bad_amounts(self, bad):
        with pytest.raises(ValidationError):
            validate_cash(bad)

    @pytest.mark.parametrize(("raw", "expected"), [("try", "TRY"), (" usd ", "USD")])
    def test_currency_normalised(self, raw, expected):
        assert validate_currency(raw) == expected

    @pytest.mark.parametrize("bad", ["EUR", "", "<script>", 42, None])
    def test_rejects_bad_currency(self, bad):
        with pytest.raises(ValidationError):
            validate_currency(bad)


class TestSetCash:
    def test_adds_new_currency(self):
        result = set_cash([], "TRY", 1000)
        assert result == [CashHolding("TRY", 1000.0)]

    def test_replaces_existing_currency(self):
        start = [make_cash("TRY", 1000)]
        result = set_cash(start, "try", 2500)
        assert result == [CashHolding("TRY", 2500.0)]

    def test_zero_removes_entry(self):
        start = [make_cash("TRY", 1000), make_cash("USD", 50)]
        result = set_cash(start, "TRY", 0)
        assert result == [CashHolding("USD", 50.0)]

    def test_does_not_mutate_input(self):
        start = [make_cash("TRY", 1000)]
        set_cash(start, "USD", 500)
        assert start == [CashHolding("TRY", 1000.0)]


class TestCashPersistence:
    def test_round_trip(self, path):
        cash = [make_cash("TRY", 12500.5), make_cash("USD", 300)]
        save_cash(cash, path)
        assert load_cash(path) == cash

    def test_saving_positions_preserves_cash(self, path):
        save_cash([make_cash("TRY", 1000)], path)
        save_portfolio([make_position("AAPL", 5, 100)], path)
        assert load_cash(path) == [CashHolding("TRY", 1000.0)]

    def test_saving_cash_preserves_positions(self, path):
        position = make_position("AAPL", 5, 100)
        save_portfolio([position], path)
        save_cash([make_cash("USD", 250)], path)
        assert load_portfolio(path) == [position]

    def test_legacy_list_file_still_loads_positions(self, path):
        payload = [{"symbol": "AAPL", "quantity": 10, "avg_cost": 150.0,
                    "currency": "USD", "added": "2026-01-01", "notes": ""}]
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert [p.symbol for p in load_portfolio(path)] == ["AAPL"]
        assert load_cash(path) == []

    def test_invalid_cash_rows_skipped(self, path):
        payload = {
            "positions": [],
            "cash": [
                {"currency": "TRY", "amount": 100},
                {"currency": "EUR", "amount": 100},
                {"currency": "USD", "amount": -5},
                "garbage",
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert load_cash(path) == [CashHolding("TRY", 100.0)]

    def test_missing_file_is_empty(self, tmp_path):
        assert load_cash(tmp_path / "nope.json") == []

    def test_duplicate_currency_keeps_last(self, path):
        payload = {"positions": [], "cash": [
            {"currency": "TRY", "amount": 100},
            {"currency": "TRY", "amount": 900},
        ]}
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert load_cash(path) == [CashHolding("TRY", 900.0)]


class TestCashTotals:
    def test_converts_both_ways(self):
        cash = [make_cash("TRY", 4000), make_cash("USD", 100)]
        totals = cash_totals(cash, usdtry=40.0)
        assert totals["try"] == pytest.approx(8000.0)
        assert totals["usd"] == pytest.approx(200.0)

    def test_empty(self):
        assert cash_totals([], 40.0) == {"try": 0.0, "usd": 0.0}


class TestCashInPortfolio:
    def _metrics(self, cash_usd=0.0):
        positions = [make_position("AAPL", 10, 100.0)]
        quotes = {"AAPL": Quote("AAPL", 100.0, 100.0, 0.0)}
        return compute_metrics(positions, quotes, {}, 40.0, cash_usd)

    def test_weight_accounts_for_cash(self):
        assert self._metrics(cash_usd=1000.0)[0].weight == pytest.approx(0.5)

    def test_weight_without_cash_is_full(self):
        assert self._metrics()[0].weight == pytest.approx(1.0)

    def test_cash_added_to_value_not_pnl(self):
        metrics = self._metrics(cash_usd=1000.0)
        totals = portfolio_totals(metrics, 40.0, [make_cash("USD", 1000)])
        assert totals["value_usd"] == pytest.approx(2000.0)
        assert totals["invested_usd"] == pytest.approx(1000.0)
        assert totals["pnl_usd"] == pytest.approx(0.0)
        assert totals["pnl_pct"] == pytest.approx(0.0)

    def test_cash_does_not_dilute_reported_pnl_pct(self):
        positions = [make_position("AAPL", 10, 100.0)]
        quotes = {"AAPL": Quote("AAPL", 110.0, 110.0, 0.0)}
        metrics = compute_metrics(positions, quotes, {}, 40.0, 5000.0)
        totals = portfolio_totals(metrics, 40.0, [make_cash("USD", 5000)])
        assert totals["pnl_pct"] == pytest.approx(10.0)

    def test_cash_weight_reported(self):
        metrics = self._metrics(cash_usd=1000.0)
        totals = portfolio_totals(metrics, 40.0, [make_cash("USD", 1000)])
        assert totals["cash_weight"] == pytest.approx(0.5)

    def test_cash_only_portfolio(self):
        totals = portfolio_totals([], 40.0, [make_cash("TRY", 8000)])
        assert totals["value_try"] == pytest.approx(8000.0)
        assert totals["value_usd"] == pytest.approx(200.0)
        assert totals["cash_weight"] == pytest.approx(1.0)
        assert totals["pnl_pct"] == 0.0

    def test_no_cash_backwards_compatible(self):
        metrics = self._metrics()
        assert portfolio_totals(metrics, 40.0) == portfolio_totals(metrics, 40.0, [])
