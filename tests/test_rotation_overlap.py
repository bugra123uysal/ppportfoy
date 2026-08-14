from portfoy.money_flow import MoneyFlowSignal
from portfoy.rotation import SectorLeader, SectorRotation
from portfoy.rotation_overlap import build_rotation_overlap
from portfoy.trade_scan import TradeSignal
from portfoy.vcp_scan import VcpCandidate


def _sector(symbol: str, quadrant: str, prev_quadrant: str = "leading") -> SectorRotation:
    return SectorRotation(
        symbol=symbol,
        label_tr=symbol,
        label_en=symbol,
        tail_x=[100.0, 101.0],
        tail_y=[100.0, 101.0],
        quadrant=quadrant,
        prev_quadrant=prev_quadrant,
        perf_1w=1.0,
        perf_1m=2.0,
        perf_3m=3.0,
    )


def _leader(symbol: str, perf_1m: float = 5.0) -> SectorLeader:
    return SectorLeader(symbol=symbol, perf_1w=1.0, perf_1m=perf_1m, perf_3m=10.0)


def _trade_signal(symbol: str, direction: str = "long") -> TradeSignal:
    return TradeSignal(
        symbol=symbol,
        sector="Enerji",
        price=100.0,
        change_1d=1.0,
        direction=direction,
        groups=[1],
        atr_14=2.0,
        suggested_stop=95.0,
        pct_from_52w_high=-5.0,
        pct_from_52w_low=20.0,
        weekly_trend_aligned=True,
    )


def _vcp_candidate(symbol: str) -> VcpCandidate:
    return VcpCandidate(
        symbol=symbol,
        sector="Enerji",
        price=100.0,
        change_1d=1.0,
        adr_pct=4.0,
        trailing_return_pct=20.0,
        range_contraction_pct=50.0,
        volume_contraction_pct=60.0,
        pct_from_52w_high=-5.0,
        suggested_stop=95.0,
    )


def _money_flow_signal(symbol: str, cmf_signal: str = "accumulation") -> MoneyFlowSignal:
    return MoneyFlowSignal(
        symbol=symbol,
        sector="Enerji",
        price=100.0,
        change_1d=1.0,
        currency="USD",
        cmf=0.2,
        cmf_signal=cmf_signal,
        mfi=55.0,
        obv_trend="yukselis",
        institutional_pct=80.0,
        insider_net_pct_6m=1.0,
    )


class TestBuildRotationOverlap:
    def test_symbol_in_leading_sector_with_long_signal_surfaces(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("COP")]}
        result = build_rotation_overlap(sectors, leaders, [_trade_signal("COP")], [], [])
        assert [c.symbol for c in result] == ["COP"]
        assert result[0].signals == ("trade_scan_long",)

    def test_improving_sector_also_counts(self):
        sectors = [_sector("XLC", "improving")]
        leaders = {"XLC": [_leader("T")]}
        result = build_rotation_overlap(sectors, leaders, [_trade_signal("T")], [], [])
        assert [c.symbol for c in result] == ["T"]

    def test_weakening_or_lagging_sector_excluded(self):
        sectors = [_sector("XLV", "weakening"), _sector("XLU", "lagging")]
        leaders = {"XLV": [_leader("MRK")], "XLU": [_leader("NEE")]}
        result = build_rotation_overlap(
            sectors, leaders, [_trade_signal("MRK"), _trade_signal("NEE")], [], []
        )
        assert result == []

    def test_sector_leader_without_any_my_trade_signal_excluded(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(sectors, leaders, [], [], [])
        assert result == []

    def test_short_signal_does_not_count_as_bullish(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(sectors, leaders, [_trade_signal("XOM", "short")], [], [])
        assert result == []

    def test_vcp_candidate_counts(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(sectors, leaders, [], [_vcp_candidate("XOM")], [])
        assert result[0].signals == ("vcp",)

    def test_money_flow_accumulation_counts(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(sectors, leaders, [], [], [_money_flow_signal("XOM")])
        assert result[0].signals == ("money_flow_accumulation",)

    def test_distribution_does_not_count_as_bullish(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(
            sectors, leaders, [], [], [_money_flow_signal("XOM", "distribution")]
        )
        assert result == []

    def test_multiple_signals_all_recorded(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(
            sectors,
            leaders,
            [_trade_signal("XOM")],
            [_vcp_candidate("XOM")],
            [_money_flow_signal("XOM")],
        )
        assert set(result[0].signals) == {"trade_scan_long", "vcp", "money_flow_accumulation"}

    def test_equal_conviction_sorted_by_performance(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("WEAK", perf_1m=1.0), _leader("STRONG", perf_1m=9.0)]}
        result = build_rotation_overlap(
            sectors, leaders, [_trade_signal("WEAK"), _trade_signal("STRONG")], [], []
        )
        assert [c.symbol for c in result] == ["STRONG", "WEAK"]

    def test_sorted_by_conviction_then_performance(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("WEAK", perf_1m=1.0), _leader("STRONG", perf_1m=9.0)]}
        result = build_rotation_overlap(
            sectors,
            leaders,
            [_trade_signal("WEAK"), _trade_signal("STRONG")],
            [],
            [_money_flow_signal("STRONG")],
        )
        assert [c.symbol for c in result] == ["STRONG", "WEAK"]

    def test_sector_label_resolved_from_config(self):
        sectors = [_sector("XLE", "leading")]
        leaders = {"XLE": [_leader("XOM")]}
        result = build_rotation_overlap(sectors, leaders, [_trade_signal("XOM")], [], [])
        assert result[0].sector == "Enerji"

    def test_no_promising_sectors_yields_empty(self):
        sectors = [_sector("XLU", "lagging")]
        result = build_rotation_overlap(sectors, {}, [_trade_signal("NEE")], [], [])
        assert result == []

    def test_empty_leaders_for_promising_sector_yields_empty(self):
        sectors = [_sector("XLE", "leading")]
        result = build_rotation_overlap(sectors, {}, [_trade_signal("XOM")], [], [])
        assert result == []
