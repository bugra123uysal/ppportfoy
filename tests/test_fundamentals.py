from portfoy.fundamentals import classify_valuation


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
