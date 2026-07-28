from datetime import date

from portfoy.calendar_events import next_nfp, upcoming_events


class TestNextNfp:
    def test_before_first_friday(self):
        # 2026-08-01 is a Saturday; first Friday of Aug 2026 is the 7th.
        assert next_nfp(date(2026, 8, 1)) == date(2026, 8, 7)

    def test_on_the_day_counts(self):
        assert next_nfp(date(2026, 8, 7)) == date(2026, 8, 7)

    def test_after_first_friday_rolls_to_next_month(self):
        assert next_nfp(date(2026, 8, 8)) == date(2026, 9, 4)

    def test_december_rolls_to_january(self):
        assert next_nfp(date(2026, 12, 10)) == date(2027, 1, 1)


class TestUpcomingEvents:
    def test_includes_fomc_inside_window(self):
        events = upcoming_events(date(2026, 7, 20), lookahead_days=15)
        fomc = [e for e in events if e.kind == "fomc"]
        assert [e.when for e in fomc] == [date(2026, 7, 29)]

    def test_excludes_fomc_outside_window(self):
        events = upcoming_events(date(2026, 7, 20), lookahead_days=5)
        assert not [e for e in events if e.kind == "fomc"]

    def test_multiple_nfps_in_long_window(self):
        events = upcoming_events(date(2026, 7, 20), lookahead_days=50)
        nfps = [e.when for e in events if e.kind == "nfp"]
        assert nfps == [date(2026, 8, 7), date(2026, 9, 4)]

    def test_earnings_included_and_labeled(self):
        earnings = {"NVDA": date(2026, 7, 30), "AAPL": None}
        events = upcoming_events(date(2026, 7, 20), earnings, lookahead_days=20)
        earn = [e for e in events if e.kind == "earnings"]
        assert len(earn) == 1 and earn[0].symbol == "NVDA"

    def test_past_earnings_excluded(self):
        earnings = {"NVDA": date(2026, 7, 10)}
        events = upcoming_events(date(2026, 7, 20), earnings)
        assert not [e for e in events if e.kind == "earnings"]

    def test_sorted_by_date(self):
        events = upcoming_events(date(2026, 7, 20), lookahead_days=45)
        dates = [e.when for e in events]
        assert dates == sorted(dates)

    def test_days_left(self):
        events = upcoming_events(date(2026, 7, 28), lookahead_days=2)
        fomc = next(e for e in events if e.kind == "fomc")
        assert fomc.days_left(date(2026, 7, 28)) == 1
