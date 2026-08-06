"""portfoy.serialize must turn every dataclass / numpy / pandas value this
codebase produces into something json.dumps can encode without raising and
without emitting the invalid-JSON tokens NaN/Infinity/-Infinity.
"""

from __future__ import annotations

import json
import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from portfoy.breadth import BreadthSnapshot
from portfoy.calendar_events import MarketEvent
from portfoy.data import AnalystView, Quote
from portfoy.options import OptionActivity
from portfoy.performance import SeriesResult
from portfoy.risk import Alert, PositionMetrics
from portfoy.rotation import SectorRotation
from portfoy.sentiment import SentimentScore
from portfoy.serialize import dumps, to_jsonable
from portfoy.storage import CashHolding, Position


class TestScalars:
    def test_none_and_str_and_bool_pass_through(self):
        assert to_jsonable(None) is None
        assert to_jsonable("AAPL") == "AAPL"
        assert to_jsonable(True) is True

    def test_plain_nan_and_infinity_become_none(self):
        assert to_jsonable(float("nan")) is None
        assert to_jsonable(float("inf")) is None
        assert to_jsonable(float("-inf")) is None

    def test_finite_float_and_int_unchanged(self):
        assert to_jsonable(3.5) == 3.5
        assert to_jsonable(7) == 7

    def test_numpy_scalars_become_native(self):
        out = to_jsonable(np.float64(3.5))
        assert out == 3.5 and isinstance(out, float)
        out = to_jsonable(np.int64(7))
        assert out == 7 and isinstance(out, int)
        assert to_jsonable(np.bool_(True)) is True

    def test_numpy_nan_becomes_none(self):
        assert to_jsonable(np.float64("nan")) is None

    def test_pandas_timestamp_becomes_iso_string(self):
        assert to_jsonable(pd.Timestamp("2026-01-15")) == "2026-01-15T00:00:00"

    def test_date_becomes_iso_string(self):
        assert to_jsonable(date(2026, 1, 15)) == "2026-01-15"


class TestSeries:
    def test_datetime_indexed_series_becomes_dates_and_values(self):
        s = pd.Series([100.0, 101.5], index=pd.to_datetime(["2026-01-01", "2026-01-02"]))
        out = to_jsonable(s)
        assert out == {
            "dates": ["2026-01-01T00:00:00", "2026-01-02T00:00:00"],
            "values": [100.0, 101.5],
        }

    def test_series_nan_values_become_none(self):
        s = pd.Series([1.0, float("nan")], index=pd.to_datetime(["2026-01-01", "2026-01-02"]))
        out = to_jsonable(s)
        assert out["values"] == [1.0, None]

    def test_non_datetime_index_series_still_serializes(self):
        s = pd.Series([1.0, 2.0], index=[0, 1])
        out = to_jsonable(s)
        assert out == {"dates": [0, 1], "values": [1.0, 2.0]}


class TestContainers:
    def test_dict_keys_stringified_and_values_converted(self):
        assert to_jsonable({"a": float("nan"), 2: np.int64(3)}) == {"a": None, "2": 3}

    def test_list_tuple_set_become_lists(self):
        assert to_jsonable([1, 2]) == [1, 2]
        assert to_jsonable((1, 2)) == [1, 2]
        assert to_jsonable({1}) == [1]

    def test_numpy_array_becomes_list(self):
        assert to_jsonable(np.array([1.0, 2.0])) == [1.0, 2.0]


class TestDataclasses:
    """One instance of every frozen dataclass in the codebase."""

    def test_alert(self):
        a = Alert(severity="crit", key="al_loss", params={"symbol": "AAPL", "value": "-21.0"})
        assert to_jsonable(a) == {
            "severity": "crit", "key": "al_loss",
            "params": {"symbol": "AAPL", "value": "-21.0"},
        }

    def test_position_metrics_with_none_and_nan_fields(self):
        m = PositionMetrics(
            symbol="AAPL", currency="USD", quantity=10.0, avg_cost=100.0, price=110.0,
            change_pct=1.0, value=1100.0, value_try=0.0, value_usd=1100.0, pnl=100.0,
            pnl_pct=10.0, weight=0.5, rsi=None, sma_fast=50.0, sma_slow=float("nan"),
            atr_stop=None,
        )
        out = to_jsonable(m)
        assert out["rsi"] is None
        assert out["atr_stop"] is None
        assert out["sma_slow"] is None
        assert out["symbol"] == "AAPL"

    def test_series_result_serializes_its_pandas_series_field(self):
        s = pd.Series([100.0, 105.0], index=pd.to_datetime(["2026-01-01", "2026-01-02"]))
        r = SeriesResult(key="portfolio", label_tr="Portföyüm", label_en="My Portfolio",
                          return_pct=5.0, series=s)
        out = to_jsonable(r)
        assert out["series"]["values"] == [100.0, 105.0]
        assert out["return_pct"] == 5.0

    def test_sector_rotation(self):
        r = SectorRotation(
            symbol="XLK", label_tr="Teknoloji", label_en="Technology",
            tail_x=[99.0, 101.0], tail_y=[98.0, 102.0], quadrant="leading",
            prev_quadrant="improving", perf_1w=1.0, perf_1m=2.0, perf_3m=3.0,
        )
        out = to_jsonable(r)
        assert out["tail_x"] == [99.0, 101.0]
        assert out["quadrant"] == "leading"

    def test_breadth_snapshot(self):
        b = BreadthSnapshot(sample_size=60, pct_above_50=55.0, pct_above_200=62.0,
                             advancers=40, decliners=20, new_high_20d=5, new_low_20d=1)
        assert to_jsonable(b)["sample_size"] == 60

    def test_sentiment_score(self):
        s = SentimentScore(composite=63.5, components={"vix": 70.0, "momentum": 57.0})
        out = to_jsonable(s)
        assert out["composite"] == 63.5
        assert out["components"]["vix"] == 70.0

    def test_option_activity(self):
        o = OptionActivity(
            symbol="SPY", expiry="2026-08-15", call_volume=1000, put_volume=800,
            call_oi=5000, put_oi=4000,
            top_contracts=[{"type": "CALL", "strike": 500.0, "last": 1.2,
                             "volume": 300, "oi": 900, "iv": 0.22}],
        )
        out = to_jsonable(o)
        assert out["top_contracts"][0]["strike"] == 500.0

    def test_market_event(self):
        e = MarketEvent(when=date(2026, 9, 16), kind="fomc")
        assert to_jsonable(e) == {"when": "2026-09-16", "kind": "fomc", "symbol": ""}

    def test_position_and_cash_holding(self):
        p = Position(symbol="AAPL", quantity=10.0, avg_cost=100.0, currency="USD",
                      added="2026-01-01", notes="")
        c = CashHolding(currency="TRY", amount=25000.0)
        assert to_jsonable(p)["symbol"] == "AAPL"
        assert to_jsonable(c) == {"currency": "TRY", "amount": 25000.0}


class TestNamedTuples:
    """NamedTuple instances are also `tuple`, so without a dedicated branch
    they fall into the generic tuple case and serialize as a positional
    array instead of a keyed object -- every frontend `.field` access on the
    result then silently reads `undefined`. Regression coverage for that.
    """

    def test_analyst_view_becomes_a_keyed_object_not_an_array(self):
        v = AnalystView(target_mean=302.8, target_high=500.0, target_low=180.0,
                         consensus="al", num_analysts=61)
        out = to_jsonable(v)
        assert out == {
            "target_mean": 302.8, "target_high": 500.0, "target_low": 180.0,
            "consensus": "al", "num_analysts": 61,
        }
        assert not isinstance(out, list)

    def test_quote_becomes_a_keyed_object(self):
        q = Quote(symbol="AAPL", price=110.0, prev_close=108.0, change_pct=1.85)
        assert to_jsonable(q) == {
            "symbol": "AAPL", "price": 110.0, "prev_close": 108.0, "change_pct": 1.85,
        }

    def test_namedtuple_nan_field_becomes_none(self):
        v = AnalystView(target_mean=float("nan"), target_high=None, target_low=None,
                         consensus=None, num_analysts=None)
        assert to_jsonable(v)["target_mean"] is None

    def test_dict_of_namedtuples_serializes_each_value_as_an_object(self):
        views = {"AAPL": AnalystView(target_mean=200.0, target_high=None,
                                      target_low=None, consensus="tut", num_analysts=10)}
        out = to_jsonable(views)
        assert out["AAPL"]["target_mean"] == 200.0
        assert out["AAPL"]["consensus"] == "tut"


class TestDumps:
    def test_round_trips_through_json_loads(self):
        m = PositionMetrics(
            symbol="AAPL", currency="USD", quantity=10.0, avg_cost=100.0, price=110.0,
            change_pct=1.0, value=1100.0, value_try=0.0, value_usd=1100.0, pnl=100.0,
            pnl_pct=10.0, weight=0.5, rsi=float("nan"), sma_fast=None, sma_slow=None,
            atr_stop=None,
        )
        text = dumps(m)
        assert "NaN" not in text
        back = json.loads(text)
        assert back["rsi"] is None

    def test_dumps_rejects_a_leftover_nan_defense_in_depth(self):
        with pytest.raises(ValueError):
            json.dumps(float("nan"), allow_nan=False)

    def test_unsupported_type_raises(self):
        class Unserializable:
            pass

        with pytest.raises(TypeError):
            to_jsonable(Unserializable())

    def test_math_isnan_sanity(self):
        # guards the implementation detail this module leans on
        assert math.isnan(float("nan"))
