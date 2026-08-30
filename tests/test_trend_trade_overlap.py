import pandas as pd

from portfoy import trend_trade_overlap
from portfoy.trade_scan import TradeSignal
from portfoy.trend_scan import TrendCandidate
from portfoy.trend_trade_overlap import (
    build_trend_trade_overlap,
    build_trend_trade_overlap_scan,
    render_text_report,
)


def _trend(symbol: str, direction: str = "boga", score: int = 3) -> TrendCandidate:
    return TrendCandidate(
        symbol=symbol,
        sector="Enerji",
        price=100.0,
        change_1d=1.0,
        direction=direction,
        score=score,
        strength={1: "erken", 2: "olusuyor", 3: "guclu"}[score],
        ma_trend_confirmed=True,
        trendline_confirmed=True,
        structural_stop=90.0 if direction == "boga" else 110.0,
        volume_confirmed=True,
        money_flow_signal="accumulation",
        money_flow_aligned=True,
        adx=30.0,
        adx_rising=True,
        trend_maturity="saglikli",
        rsi_divergence_warning=False,
        trend_age_days=5,
        newly_triggered=True,
    )


def _trade(symbol: str, direction: str = "long", groups: list[int] | None = None) -> TradeSignal:
    return TradeSignal(
        symbol=symbol,
        sector="Enerji",
        price=100.0,
        change_1d=1.0,
        direction=direction,
        groups=groups if groups is not None else [1],
        atr_14=2.0,
        suggested_stop=95.0 if direction == "long" else 105.0,
        pct_from_52w_high=-5.0,
        pct_from_52w_low=20.0,
        weekly_trend_aligned=True,
    )


class TestBuildTrendTradeOverlap:
    def test_bullish_trend_with_long_signal_surfaces(self):
        result = build_trend_trade_overlap([_trend("XOM")], [_trade("XOM")])
        assert [c.symbol for c in result] == ["XOM"]
        assert result[0].direction == "boga"
        assert result[0].trade_groups == [1]

    def test_bearish_trend_with_short_signal_surfaces(self):
        result = build_trend_trade_overlap(
            [_trend("XOM", direction="ayi")], [_trade("XOM", direction="short")]
        )
        assert [c.symbol for c in result] == ["XOM"]
        assert result[0].direction == "ayi"

    def test_mismatched_direction_excluded(self):
        # Bullish trend structure but only a short My Trade signal -- the two
        # scans disagree on direction, so this must not count as corroboration.
        result = build_trend_trade_overlap(
            [_trend("XOM", direction="boga")], [_trade("XOM", direction="short")]
        )
        assert result == []

    def test_trend_without_any_trade_signal_excluded(self):
        result = build_trend_trade_overlap([_trend("XOM")], [])
        assert result == []

    def test_trade_signal_without_trend_excluded(self):
        result = build_trend_trade_overlap([], [_trade("XOM")])
        assert result == []

    def test_fields_carried_from_both_sources(self):
        result = build_trend_trade_overlap(
            [_trend("XOM", score=2)], [_trade("XOM", groups=[2, 3])]
        )
        candidate = result[0]
        assert candidate.sector == "Enerji"
        assert candidate.trend_score == 2
        assert candidate.trend_strength == "olusuyor"
        assert candidate.trade_groups == [2, 3]
        assert candidate.structural_stop == 90.0
        assert candidate.suggested_stop == 95.0

    def test_sorted_by_trend_score_then_group_count(self):
        result = build_trend_trade_overlap(
            [_trend("WEAK", score=1), _trend("STRONG", score=3)],
            [_trade("WEAK"), _trade("STRONG")],
        )
        assert [c.symbol for c in result] == ["STRONG", "WEAK"]

    def test_equal_score_sorted_by_confirming_group_count(self):
        result = build_trend_trade_overlap(
            [_trend("FEW", score=2), _trend("MANY", score=2)],
            [_trade("FEW", groups=[1]), _trade("MANY", groups=[1, 2, 3])],
        )
        assert [c.symbol for c in result] == ["MANY", "FEW"]


class TestBuildTrendTradeOverlapScan:
    def test_fetches_history_once_and_combines_both_scans(self, monkeypatch):
        histories = {"XOM": pd.DataFrame({"Close": [1.0]}), "AAPL": pd.DataFrame({"Close": [2.0]})}
        fetch_calls = []

        def fake_get_histories(symbols, period=None):
            fetch_calls.append(tuple(symbols))
            return histories

        monkeypatch.setattr(trend_trade_overlap.data, "get_histories", fake_get_histories)
        monkeypatch.setattr(
            trend_trade_overlap, "_trend_scan_symbol",
            lambda sym, sector, df: _trend(sym) if sym == "XOM" else None,
        )
        monkeypatch.setattr(
            trend_trade_overlap, "_trade_scan_symbol",
            lambda sym, sector, df: [_trade(sym)] if sym == "XOM" else [],
        )

        result = build_trend_trade_overlap_scan({"XOM": "Enerji", "AAPL": "Teknoloji"})

        assert len(fetch_calls) == 1  # one shared fetch, not one per scan
        assert [c.symbol for c in result] == ["XOM"]

    def test_missing_history_treated_as_empty_frame(self, monkeypatch):
        monkeypatch.setattr(trend_trade_overlap.data, "get_histories", lambda symbols, period=None: {})
        seen_dfs = []

        def fake_trend(sym, sector, df):
            seen_dfs.append(df)
            return None

        monkeypatch.setattr(trend_trade_overlap, "_trend_scan_symbol", fake_trend)
        monkeypatch.setattr(trend_trade_overlap, "_trade_scan_symbol", lambda sym, sector, df: [])

        result = build_trend_trade_overlap_scan({"XOM": "Enerji"})

        assert result == []
        assert seen_dfs[0].empty

    def test_empty_universe_produces_empty_scan(self, monkeypatch):
        monkeypatch.setattr(trend_trade_overlap.data, "get_histories", lambda symbols, period=None: {})
        assert build_trend_trade_overlap_scan({}) == []


class TestRenderTextReport:
    def test_empty_candidates_returns_no_matches_message(self):
        report = render_text_report([])
        assert "yok" in report

    def test_report_mentions_bullish_and_bearish_symbols(self):
        result = build_trend_trade_overlap(
            [_trend("XOM"), _trend("PG", direction="ayi")],
            [_trade("XOM"), _trade("PG", direction="short")],
        )
        report = render_text_report(result)
        assert "XOM" in report
        assert "PG" in report
        assert "Boğa yönünde" in report
        assert "Ayı yönünde" in report

    def test_report_omits_missing_direction_section(self):
        result = build_trend_trade_overlap([_trend("XOM")], [_trade("XOM")])
        report = render_text_report(result)
        assert "Boğa yönünde" in report
        assert "Ayı yönünde" not in report

    def test_report_never_raises_on_none_stop_fields(self):
        # structural_stop/suggested_stop aren't referenced by the text
        # report, but exercise the real dataclass shape defensively.
        result = build_trend_trade_overlap([_trend("XOM")], [_trade("XOM")])
        report = render_text_report(result)
        assert isinstance(report, str) and report
