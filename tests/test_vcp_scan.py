import numpy as np
import pandas as pd
import pytest

from portfoy import vcp_scan
from portfoy.vcp_scan import VcpCandidate, build_vcp_scan, scan_symbol

N1, N2 = 50, 20  # prior-rally phase, then a tight-consolidation tail


PHASE1_TOP = 140.0  # shared level every _df() variant rallies to / consolidates around


def _df(
    phase1: str = "rally",
    phase2: str = "tight_up",
    adr_band: tuple[float, float] = (1.018, 0.982),
    vol_drop: bool = True,
) -> pd.DataFrame:
    """A 70-bar fixture whose defaults satisfy every VCP gate (verified
    against the real thresholds in config.py) -- each parameter flips
    exactly one gate to failing, isolating what each test claims to test.
    """
    close1 = (
        np.linspace(100.0, PHASE1_TOP, N1) if phase1 == "rally" else np.full(N1, PHASE1_TOP)
    )
    if phase2 == "tight_up":
        close2 = np.array([PHASE1_TOP + (i + 1) * 0.4 for i in range(N2)])
    elif phase2 == "wide":
        close2 = PHASE1_TOP + 8.0 * np.sin(np.linspace(0, 6 * np.pi, N2))
    elif phase2 == "decline":
        close2 = np.array([PHASE1_TOP - (i + 1) * 0.3 for i in range(N2)])
    else:
        raise ValueError(phase2)

    close = np.concatenate([close1, close2])
    high = close * adr_band[0]
    low = close * adr_band[1]
    volume = np.concatenate(
        [
            np.full(N1, 3_000_000.0),
            np.full(N2, 1_000_000.0 if vol_drop else 3_000_000.0),
        ]
    )
    return pd.DataFrame({"Open": close, "High": high, "Low": low, "Close": close, "Volume": volume})


class TestScanSymbol:
    def test_fires_when_every_gate_is_satisfied(self):
        candidate = scan_symbol("AAA", "Teknoloji", _df())
        assert isinstance(candidate, VcpCandidate)
        assert candidate.symbol == "AAA"
        assert candidate.sector == "Teknoloji"
        assert candidate.price == pytest.approx(148.0)
        assert candidate.adr_pct > 3.0
        assert candidate.trailing_return_pct > 15.0
        assert candidate.range_contraction_pct < 60.0
        assert candidate.volume_contraction_pct < 70.0
        assert candidate.pct_from_52w_high == pytest.approx(0.0)
        assert candidate.suggested_stop is not None
        assert candidate.suggested_stop < candidate.price

    def test_none_on_empty_history(self):
        assert scan_symbol("AAA", "Teknoloji", pd.DataFrame()) is None

    def test_none_on_insufficient_history(self):
        short = _df().iloc[-30:].reset_index(drop=True)
        assert scan_symbol("AAA", "Teknoloji", short) is None

    def test_none_below_adr_threshold(self):
        # A near-flat daily high/low band -- not enough of a "mover".
        df = _df(adr_band=(1.005, 0.995))
        assert scan_symbol("AAA", "Teknoloji", df) is None

    def test_none_without_prior_rally(self):
        # Flat lead-in instead of a big 3-month move before consolidating.
        df = _df(phase1="flat")
        assert scan_symbol("AAA", "Teknoloji", df) is None

    def test_none_without_range_contraction(self):
        # The "tight" tail is just as wide as the prior baseline -- no VCP.
        df = _df(phase2="wide")
        assert scan_symbol("AAA", "Teknoloji", df) is None

    def test_none_without_volume_contraction(self):
        # Volume stays flat instead of drying up into the consolidation.
        df = _df(vol_drop=False)
        assert scan_symbol("AAA", "Teknoloji", df) is None

    def test_none_when_price_is_below_ema(self):
        # A declining tail ends below its own EMA10/EMA20.
        df = _df(phase2="decline")
        assert scan_symbol("AAA", "Teknoloji", df) is None

    def test_none_when_too_far_from_52w_high(self):
        # A higher earlier peak (180), a *gradual* decline down to the
        # consolidation base (140, > 15% off the peak) so EMA10/EMA20 have
        # settled near the new level, then the same tight-consolidation
        # tail as the passing fixture -- every other gate still passes
        # (verified), isolating the 52w-high-proximity check. An abrupt
        # jump straight from the peak into consolidation (no decline
        # segment) would instead trip the EMA gate first, since a 20-bar
        # EMA doesn't have time to catch up to a sudden ~22% drop -- that
        # false-isolation bug is why this fixture has three phases.
        n1a, n1b = 40, 10
        close1a = np.linspace(100.0, 180.0, n1a)
        close1b = np.linspace(180.0, 140.0, n1b + 1)[1:]  # drop the duplicate 180 at the seam
        close2 = np.array([140.0 + (i + 1) * 0.4 for i in range(N2)])
        close = np.concatenate([close1a, close1b, close2])
        high, low = close * 1.018, close * 0.982
        volume = np.concatenate([np.full(n1a + n1b, 3_000_000.0), np.full(N2, 1_000_000.0)])
        df = pd.DataFrame(
            {"Open": close, "High": high, "Low": low, "Close": close, "Volume": volume}
        )
        assert scan_symbol("AAA", "Teknoloji", df) is None


class TestBuildVcpScan:
    def test_skips_symbols_with_insufficient_history(self, monkeypatch):
        monkeypatch.setattr(vcp_scan.data, "get_histories", lambda symbols, period=None: {})
        assert build_vcp_scan({"AAA": "Test"}) == []

    def test_includes_and_labels_matching_symbols(self, monkeypatch):
        histories = {"AAA": _df(), "BBB": pd.DataFrame()}
        monkeypatch.setattr(
            vcp_scan.data, "get_histories", lambda symbols, period=None: histories
        )
        out = build_vcp_scan({"AAA": "Enerji", "BBB": "Finans"})
        assert [c.symbol for c in out] == ["AAA"]
        assert out[0].sector == "Enerji"

    def test_empty_universe_produces_empty_scan(self, monkeypatch):
        monkeypatch.setattr(vcp_scan.data, "get_histories", lambda symbols, period=None: {})
        assert build_vcp_scan({}) == []
