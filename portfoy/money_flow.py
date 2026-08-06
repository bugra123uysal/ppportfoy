"""My Trade sermaye akışı (money flow) scan.

Combines two free, complementary signals per stock:

  Teknik (günlük, fiyat+hacimden): Chaikin Money Flow (accumulation/
  distribution), Money Flow Index (hacim ağırlıklı momentum), On-Balance
  Volume trendi (kısa vadeli teyit).
  Filing bazlı (periyodik, gerçek veri): kurumsal sahiplik yüzdesi ve son
  6 ayda içeriden net alım/satım (SEC 13F/Form 4'ün Yahoo üzerindeki bedava
  görünümü -- data.get_ownership_flow).

Bu bir al/sat sinyali değil, bilgilendirme amaçlı bir tablodur -- yatırım
tavsiyesi değildir.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data
from .indicators import chaikin_money_flow, money_flow_index, on_balance_volume, pct_change_last


@dataclass(frozen=True)
class MoneyFlowSignal:
    symbol: str
    sector: str
    price: float
    change_1d: float
    cmf: float | None
    cmf_signal: str              # "accumulation" | "distribution" | "notr"
    mfi: float | None
    obv_trend: str               # "yukselis" | "dusus" | "yatay"
    institutional_pct: float | None
    insider_net_pct_6m: float | None


def _cmf_signal(value: float | None) -> str:
    if value is None:
        return "notr"
    if value > config.CMF_THRESHOLD:
        return "accumulation"
    if value < -config.CMF_THRESHOLD:
        return "distribution"
    return "notr"


def _obv_trend(obv: pd.Series) -> str:
    lookback = config.OBV_TREND_LOOKBACK
    if len(obv) <= lookback:
        return "yatay"
    current, past = obv.iloc[-1], obv.iloc[-1 - lookback]
    if pd.isna(current) or pd.isna(past):
        return "yatay"
    if current > past:
        return "yukselis"
    if current < past:
        return "dusus"
    return "yatay"


def scan_symbol(symbol: str, sector: str, df: pd.DataFrame) -> MoneyFlowSignal | None:
    """The part of `build_money_flow_scan` that doesn't fetch history -- pure
    per-symbol scoring against an already-fetched frame (the ownership read
    is still its own cached network call; it isn't part of `df`). Split out
    so callers who already have `df` (position_health.py, reusing
    `_load_metrics`'s history) don't need a second round trip.
    """
    if df.empty or len(df) < config.CMF_PERIOD:
        return None

    cmf = chaikin_money_flow(df["High"], df["Low"], df["Close"], df["Volume"], config.CMF_PERIOD)
    mfi = money_flow_index(df["High"], df["Low"], df["Close"], df["Volume"], config.MFI_PERIOD)
    obv = on_balance_volume(df["Close"], df["Volume"])

    cmf_last = None if cmf.empty or pd.isna(cmf.iloc[-1]) else float(cmf.iloc[-1])
    mfi_last = None if mfi.empty or pd.isna(mfi.iloc[-1]) else float(mfi.iloc[-1])
    ownership = data.get_ownership_flow(symbol)

    return MoneyFlowSignal(
        symbol=symbol,
        sector=sector,
        price=float(df["Close"].iloc[-1]),
        change_1d=pct_change_last(df["Close"]),
        cmf=cmf_last,
        cmf_signal=_cmf_signal(cmf_last),
        mfi=mfi_last,
        obv_trend=_obv_trend(obv),
        institutional_pct=ownership.institutional_pct if ownership else None,
        insider_net_pct_6m=ownership.insider_net_pct_6m if ownership else None,
    )


def build_money_flow_scan(universe: dict[str, str]) -> list[MoneyFlowSignal]:
    """Scan `universe` (ticker -> sector label) for money-flow signals."""
    histories = data.get_histories(tuple(universe), period=config.MONEY_FLOW_HISTORY_PERIOD)
    results: list[MoneyFlowSignal] = []
    for symbol, sector in universe.items():
        signal = scan_symbol(symbol, sector, histories.get(symbol, pd.DataFrame()))
        if signal is not None:
            results.append(signal)
    return results
