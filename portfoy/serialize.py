"""JSON-safe serialization for API responses.

Nothing in this codebase's dataclasses is guaranteed to survive
``json.dumps`` untouched: ``pandas``/``numpy`` computations routinely
produce ``NaN`` (bare ``NaN``/``Infinity`` are not valid JSON and blow up
``JSON.parse`` on the client), ``np.float64``/``np.int64`` scalars, and
``pd.Timestamp``/``pd.Series`` values that ``json`` has no encoder for.

Every value that leaves an API route goes through :func:`to_jsonable` (or
:func:`dumps`, which wraps it) so this failure mode is caught once, here,
instead of resurfacing per-endpoint in production.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import math
from typing import Any

import numpy as np
import pandas as pd


def to_jsonable(value: Any) -> Any:
    """Recursively convert a value into plain, JSON-encodable Python types.

    NaN/Infinity (Python float or numpy) become ``None``. numpy scalars
    become native ``float``/``int``/``bool``. Dates and pandas Timestamps
    become ISO-8601 strings. A ``pd.Series`` becomes
    ``{"dates": [...], "values": [...]}``. Dataclass instances become
    dicts of their fields, recursively converted.
    """
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.floating):
        as_float = float(value)
        return as_float if math.isfinite(as_float) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, pd.Series):
        return _series_to_jsonable(value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return [to_jsonable(v) for v in value.tolist()]
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    raise TypeError(f"portfoy.serialize cannot encode {type(value)!r}: {value!r}")


def dumps(value: Any, **kwargs: Any) -> str:
    """Serialize a value to a JSON string, routed through :func:`to_jsonable`.

    ``allow_nan=False`` is a second line of defense: by the time ``json``
    sees the converted value there should be no NaN/Infinity left, so this
    only fires if a new numeric type slips past ``to_jsonable`` uncaught.
    """
    kwargs.setdefault("allow_nan", False)
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(to_jsonable(value), **kwargs)


def _series_to_jsonable(series: pd.Series) -> dict:
    index = series.index
    if isinstance(index, pd.DatetimeIndex):
        dates: list[Any] = [ts.isoformat() for ts in index]
    else:
        dates = [to_jsonable(i) for i in index]
    return {"dates": dates, "values": [to_jsonable(v) for v in series.to_numpy()]}
