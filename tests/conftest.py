import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _no_nemotron_api_key(monkeypatch):
    """commentary._ask() short-circuits to None whenever NVIDIA_API_KEY is
    unset -- scrub it for every test so payload tests stay deterministic
    (no real network call) regardless of what's in the host environment.
    Tests that actually exercise the Nemotron call path set it back via
    monkeypatch.setenv."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
