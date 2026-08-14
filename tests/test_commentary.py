import requests

from portfoy import commentary, config
from portfoy.breadth import BreadthSnapshot
from portfoy.money_flow import MoneyFlowSignal
from portfoy.movers import Mover
from portfoy.rotation import SectorRotation
from portfoy.rotation_overlap import OverlapCandidate
from portfoy.sentiment import SentimentScore
from portfoy.vcp_scan import VcpCandidate
from portfoy.yield_curve import YieldCurveSnapshot


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> dict:
        return self._payload


def _ok_response(text: str = "Ne oldu -> neden -> ders.") -> _FakeResponse:
    return _FakeResponse({"choices": [{"message": {"content": text}}]})


class TestAsk:
    def test_returns_none_without_api_key(self, monkeypatch):
        def _raise_if_called(*args, **kwargs):
            raise AssertionError("requests.post should not run without an API key")

        monkeypatch.setattr(commentary.requests, "post", _raise_if_called)
        assert commentary._ask("some-model", {"a": 1}) is None

    def test_returns_stripped_content_on_success(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(
            commentary.requests, "post", lambda *a, **k: _ok_response("  merhaba  ")
        )
        assert commentary._ask("some-model", {"a": 1}) == "merhaba"

    def test_sends_model_and_bearer_header(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _ok_response()

        monkeypatch.setattr(commentary.requests, "post", fake_post)
        commentary._ask(config.NEMOTRON_ULTRA_MODEL, {"sembol": "AAPL"})
        assert captured["url"] == f"{config.NEMOTRON_API_BASE}/chat/completions"
        assert captured["headers"]["Authorization"] == "Bearer test-key"
        assert captured["json"]["model"] == config.NEMOTRON_ULTRA_MODEL

    def test_disables_thinking_mode(self, monkeypatch):
        """Regression guard: confirmed against the live API that Nemotron 3
        defaults to "thinking" mode, which leaks its chain-of-thought
        reasoning straight into `content` instead of a clean answer unless
        chat_template_kwargs.enable_thinking is explicitly turned off."""
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["json"] = json
            return _ok_response()

        monkeypatch.setattr(commentary.requests, "post", fake_post)
        commentary._ask("some-model", {})
        assert captured["json"]["chat_template_kwargs"] == {"enable_thinking": False}

    def test_returns_none_on_request_exception(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

        def _raise(*args, **kwargs):
            raise requests.ConnectionError("boom")

        monkeypatch.setattr(commentary.requests, "post", _raise)
        assert commentary._ask("some-model", {}) is None

    def test_returns_none_on_http_error_status(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(commentary.requests, "post", lambda *a, **k: _FakeResponse({}, 429))
        assert commentary._ask("some-model", {}) is None

    def test_returns_none_on_malformed_body(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(
            commentary.requests, "post", lambda *a, **k: _FakeResponse({"unexpected": True})
        )
        assert commentary._ask("some-model", {}) is None


class TestWrappersSkipCallWhenNothingToSay:
    """Every wrapper must short-circuit to None -- no _ask call at all --
    when its input carries nothing worth narrating, regardless of whether
    an API key is configured."""

    def test_money_flow_empty_list(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(commentary, "_ask", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
        assert commentary.money_flow_commentary([]) is None

    def test_money_flow_all_neutral(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(commentary, "_ask", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
        neutral = MoneyFlowSignal(
            symbol="AAPL", sector="Teknoloji", price=200.0, change_1d=1.0, currency="USD",
            cmf=0.0, cmf_signal="notr", mfi=50.0, obv_trend="yatay",
            institutional_pct=None, insider_net_pct_6m=None,
        )
        assert commentary.money_flow_commentary([neutral]) is None

    def test_rotation_empty(self):
        assert commentary.rotation_commentary([]) is None

    def test_rotation_overlap_empty(self):
        assert commentary.rotation_overlap_commentary([]) is None

    def test_vcp_empty(self):
        assert commentary.vcp_commentary([]) is None

    def test_movers_empty(self):
        assert commentary.movers_commentary([], []) is None

    def test_market_pulse_all_none(self):
        assert commentary.market_pulse_commentary(None, None, None, []) is None


class TestWrappersCallTheRightModel:
    def test_symbol_report_uses_ultra(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            commentary, "_ask",
            lambda model, payload, **k: captured.update(model=model, payload=payload) or "yorum",
        )

        class _Fib:
            nearest_ratio = 0.5
            zone_label = "0.382 - 0.5 arası"
            pct_to_nearest = -1.2

        class _Report:
            symbol = "AAPL"
            price = 200.0
            change_1d = 1.0
            ema21_rising = True
            ema50_rising = True
            price_vs_sma50 = "ustunde"
            price_vs_sma200 = "ustunde"
            weekly_trend_aligned = True
            rsi = 55.0
            rsi_zone = "notr"
            obv_trend = "yukselis"
            cmf = 0.1
            cmf_signal = "accumulation"
            mfi = 60.0
            pct_from_52w_high = -5.0
            pct_from_52w_low = 30.0
            fib = _Fib()

        result = commentary.symbol_report_commentary(_Report(), None)
        assert result == "yorum"
        assert captured["model"] == config.NEMOTRON_ULTRA_MODEL
        assert captured["payload"]["sembol"] == "AAPL"
        assert captured["payload"]["fibonacci"]["en_yakin_seviye"] == 0.5

    def test_money_flow_uses_super_and_only_top_names(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            commentary, "_ask",
            lambda model, payload, **k: captured.update(model=model, payload=payload) or "yorum",
        )
        accumulation = MoneyFlowSignal(
            symbol="AAPL", sector="Teknoloji", price=200.0, change_1d=1.0, currency="USD",
            cmf=0.3, cmf_signal="accumulation", mfi=70.0, obv_trend="yukselis",
            institutional_pct=60.0, insider_net_pct_6m=1.0,
        )
        result = commentary.money_flow_commentary([accumulation])
        assert result == "yorum"
        assert captured["model"] == config.NEMOTRON_SUPER_MODEL
        assert captured["payload"]["birikim_yapan_ust5"][0]["sembol"] == "AAPL"
        assert captured["payload"]["dagitim_yapan_ust5"] == []

    def test_rotation_uses_super(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            commentary, "_ask",
            lambda model, payload, **k: captured.update(model=model) or "yorum",
        )
        sector = SectorRotation(
            symbol="XLK", label_tr="Teknoloji", label_en="Technology",
            tail_x=[1.0], tail_y=[1.0], quadrant="leading", prev_quadrant="improving",
            perf_1w=1.0, perf_1m=2.0, perf_3m=5.0,
        )
        assert commentary.rotation_commentary([sector]) == "yorum"
        assert captured["model"] == config.NEMOTRON_SUPER_MODEL

    def test_rotation_overlap_uses_super(self, monkeypatch):
        monkeypatch.setattr(commentary, "_ask", lambda model, payload, **k: model)
        candidate = OverlapCandidate(
            symbol="AAPL", sector="Teknoloji", perf_1m=5.0, signals=("trade_scan_long",)
        )
        assert commentary.rotation_overlap_commentary([candidate]) == config.NEMOTRON_SUPER_MODEL

    def test_vcp_uses_super(self, monkeypatch):
        monkeypatch.setattr(commentary, "_ask", lambda model, payload, **k: model)
        candidate = VcpCandidate(
            symbol="AAPL", sector="Teknoloji", price=200.0, change_1d=1.0, adr_pct=4.0,
            trailing_return_pct=20.0, range_contraction_pct=50.0, volume_contraction_pct=60.0,
            pct_from_52w_high=-5.0, suggested_stop=190.0,
        )
        assert commentary.vcp_commentary([candidate]) == config.NEMOTRON_SUPER_MODEL

    def test_movers_uses_super(self, monkeypatch):
        monkeypatch.setattr(commentary, "_ask", lambda model, payload, **k: model)
        mover = Mover(
            symbol="AAPL", name="Apple", price=200.0, change_pct=8.0, volume=1_000_000,
            avg_volume_3m=500_000, relative_volume=2.0, sector="Teknoloji", signals=[], news=[],
        )
        assert commentary.movers_commentary([mover], []) == config.NEMOTRON_SUPER_MODEL

    def test_market_pulse_uses_super(self, monkeypatch):
        monkeypatch.setattr(commentary, "_ask", lambda model, payload, **k: model)
        breadth = BreadthSnapshot(
            sample_size=60, pct_above_50=55.0, pct_above_200=65.0, advancers=40, decliners=20,
            new_high_20d=10, new_low_20d=2, trin=0.9, mcclellan=30.0,
        )
        sentiment = SentimentScore(composite=60.0, components={"vix": 70.0})
        yield_curve = YieldCurveSnapshot(
            yield_10y=4.0, yield_3m=5.0, spread_10y_3m=-1.0, inverted=True,
            credit_spread_proxy_change=-1.0, credit_stress=False,
        )
        macro = [{"symbol": "^GSPC", "label": "S&P 500", "price": 5000.0, "change_pct": 0.5}]
        result = commentary.market_pulse_commentary(breadth, sentiment, yield_curve, macro)
        assert result == config.NEMOTRON_SUPER_MODEL
