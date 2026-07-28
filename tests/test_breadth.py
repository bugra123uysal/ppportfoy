import numpy as np
import pandas as pd
import pytest

from portfoy.breadth import (
    advance_decline,
    build_snapshot,
    new_highs_lows,
    pct_above_ma,
)

DAYS = 260


def _closes(**series) -> pd.DataFrame:
    index = pd.date_range("2025-07-01", periods=DAYS, freq="B")
    return pd.DataFrame(series, index=index)


def _universe() -> pd.DataFrame:
    """Two rising stocks, one falling, one flat-ish."""
    return _closes(
        UP1=np.linspace(100.0, 200.0, DAYS),
        UP2=np.linspace(50.0, 90.0, DAYS),
        DOWN=np.linspace(200.0, 100.0, DAYS),
        FLAT=np.full(DAYS, 100.0),
    )


class TestPctAboveMa:
    def test_rising_stocks_counted_above(self):
        pct = pct_above_ma(_universe(), 50)
        assert pct.iloc[-1] == pytest.approx(50.0)  # UP1, UP2 above; DOWN below; FLAT == MA

    def test_all_rising_is_100(self):
        frame = _closes(A=np.linspace(1, 2, DAYS), B=np.linspace(3, 9, DAYS))
        assert pct_above_ma(frame, 50).iloc[-1] == pytest.approx(100.0)

    def test_warmup_period_excluded(self):
        pct = pct_above_ma(_universe(), 200)
        assert len(pct) == DAYS - 199

    def test_empty_frame(self):
        assert pct_above_ma(pd.DataFrame(), 50).empty


class TestAdvanceDecline:
    def test_counts_todays_moves(self):
        adv, dec = advance_decline(_universe())
        assert adv == 2 and dec == 1  # FLAT is unchanged, counts as neither

    def test_too_short(self):
        assert advance_decline(_closes(A=[100.0][:1])) == (0, 0)


class TestNewHighsLows:
    def test_trending_stocks_at_extremes(self):
        highs, lows = new_highs_lows(_universe(), window=20)
        assert highs >= 2   # both risers end at a 20-day high (FLAT ties both ways)
        assert lows >= 1    # the faller ends at a 20-day low

    def test_short_history(self):
        assert new_highs_lows(_universe().head(5), window=20) == (0, 0)


class TestBuildSnapshot:
    def test_full_snapshot(self):
        snap = build_snapshot(_universe())
        assert snap is not None
        assert snap.sample_size == 4
        assert snap.advancers == 2
        assert 0 <= snap.pct_above_200 <= 100

    def test_health_bands(self):
        healthy = build_snapshot(
            _closes(A=np.linspace(1, 2, DAYS), B=np.linspace(1, 3, DAYS),
                    C=np.linspace(2, 5, DAYS))
        )
        assert healthy.health == "healthy"
        weak = build_snapshot(
            _closes(A=np.linspace(2, 1, DAYS), B=np.linspace(3, 1, DAYS),
                    C=np.linspace(5, 2, DAYS))
        )
        assert weak.health == "weak"

    def test_empty_returns_none(self):
        assert build_snapshot(pd.DataFrame()) is None
