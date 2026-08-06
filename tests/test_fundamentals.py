from portfoy.data import FundamentalMetrics
from portfoy.fundamentals import build_fundamental_scan, classify_valuation


class TestClassifyValuation:
    def test_cheap_peg_and_ev_ebitda_is_ucuz(self):
        assert classify_valuation(peg=0.7, ev_ebitda=8.0, revenue_growth=10.0,
                                   operating_margin=15.0) == "ucuz"

    def test_expensive_peg_and_ev_ebitda_is_pahali(self):
        assert classify_valuation(peg=3.0, ev_ebitda=20.0, revenue_growth=10.0,
                                   operating_margin=15.0) == "pahali"

    def test_mixed_signals_is_makul(self):
        # PEG cheap (+1), EV/EBITDA expensive (-1) -> net 0.
        assert classify_valuation(peg=0.5, ev_ebitda=20.0, revenue_growth=10.0,
                                   operating_margin=15.0) == "makul"

    def test_no_data_is_belirsiz(self):
        assert classify_valuation(peg=None, ev_ebitda=None, revenue_growth=None,
                                   operating_margin=None) == "belirsiz"

    def test_cheap_multiples_on_deteriorating_business_is_capped_pahali(self):
        # Statistically "ucuz" (PEG + EV/EBITDA both cheap) but shrinking
        # revenue with a negative operating margin -- a value trap, not a
        # bargain, so the verdict must not read "ucuz".
        assert classify_valuation(peg=0.5, ev_ebitda=5.0, revenue_growth=-5.0,
                                   operating_margin=-2.0) == "pahali"

    def test_ev_ebitda_alone_still_classifies(self):
        assert classify_valuation(peg=None, ev_ebitda=8.0, revenue_growth=None,
                                   operating_margin=None) == "ucuz"


class TestBuildFundamentalScan:
    def test_skips_symbols_with_no_data(self, monkeypatch):
        import portfoy.fundamentals as fundamentals_mod

        monkeypatch.setattr(fundamentals_mod.data, "get_fundamentals", lambda sym: None)
        assert build_fundamental_scan({"AAA": "Test"}) == []

    def test_builds_snapshot_for_available_symbols(self, monkeypatch):
        import portfoy.fundamentals as fundamentals_mod

        metrics = FundamentalMetrics(
            pe=18.0, peg=0.8, ev_ebitda=9.0, revenue_growth=12.0,
            gross_margin=40.0, operating_margin=20.0, roe=25.0,
            debt_to_equity=0.5, fcf_yield=4.0,
        )
        monkeypatch.setattr(
            fundamentals_mod.data, "get_fundamentals",
            lambda sym: metrics if sym == "AAA" else None,
        )
        out = build_fundamental_scan({"AAA": "Enerji", "BBB": "Finans"})
        assert [s.symbol for s in out] == ["AAA"]

        signal = out[0]
        assert signal.sector == "Enerji"
        assert signal.pe == 18.0
        assert signal.peg == 0.8
        assert signal.ev_ebitda == 9.0
        assert signal.revenue_growth == 12.0
        assert signal.roe == 25.0
        assert signal.verdict == "ucuz"
