"""Hisse Raporu -- on-demand single-symbol technical report.

Not a scanner (doesn't sweep a universe) and not a forecaster: this reads the
same indicators My Trade's scanners already compute (trade_scan.py,
vcp_scan.py, money_flow.py) for exactly one symbol at a time, on request, and
reports the *current mechanical state* -- trend, momentum, volatility/
structure, volume, and distance from the 52-week range -- plus which of the
existing trade_scan.py groups currently match. `summary_tr` stitches that
state into a short Turkish paragraph with plain string formatting; nothing
here calls a model or predicts a future price. Same "mechanical, not
investment advice" spirit as every other My Trade module.

Works for any US ticker Yahoo covers, not just the curated
SECTOR_LEADER_STOCKS pool the scanners use -- this is a lookup tool, not a
sweep, so there's no universe to curate.

Pure functions only -- data fetching lives in data.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data, money_flow, trade_scan
from .indicators import (
    atr,
    average_daily_range_pct,
    chaikin_money_flow,
    ema,
    last_value,
    money_flow_index,
    on_balance_volume,
    pct_change_last,
    pct_from_52w_high,
    pct_from_52w_low,
    range_pct,
    sma,
    stochastic_momentum_index,
    stochastic_rsi,
    volume_sma,
    weekly_trend_up,
)
from .indicators import rsi as rsi_indicator


@dataclass(frozen=True)
class SymbolReport:
    symbol: str
    price: float
    change_1d: float

    # Trend
    ema21_rising: bool | None
    ema50_rising: bool | None
    price_vs_sma50: str | None      # "ustunde" | "altinda" | None
    price_vs_sma200: str | None
    weekly_trend_aligned: bool | None   # weekly EMA(10) still rising

    # Momentum
    rsi: float | None
    rsi_zone: str | None            # "asiri_alim" | "asiri_satim" | "notr"
    stoch_rsi_k: float | None
    stoch_rsi_d: float | None
    smi: float | None
    smi_signal: float | None

    # Volatility / structure
    atr_14: float | None
    adr_pct: float | None
    range_contraction_pct: float | None     # last 10d range / last 40d range * 100
    volume_contraction_pct: float | None    # last 10d avg volume / last 50d avg * 100

    # Volume
    volume_vs_avg_pct: float | None         # last volume vs its own 20d average
    obv_trend: str                          # "yukselis" | "dusus" | "yatay"
    cmf: float | None
    cmf_signal: str                         # "accumulation" | "distribution" | "notr"
    mfi: float | None

    # Position in the 52-week range
    pct_from_52w_high: float | None
    pct_from_52w_low: float | None

    # Cross-reference against My Trade's own trade_scan.py groups
    matched_long_groups: list[int]
    matched_short_groups: list[int]

    summary_tr: str


def _ema_rising(close: pd.Series, period: int) -> bool | None:
    """Same slope check trade_scan.py's Group 2 uses -- current EMA vs its
    value 5 bars back (`.iloc[-6]`). None if there isn't enough history yet,
    not a false reading."""
    values = ema(close, period)
    if len(values) < 6 or values.iloc[-6:].isna().any():
        return None
    return bool(values.iloc[-1] > values.iloc[-6])


def _price_vs_level(price: float, level: float | None) -> str | None:
    if level is None:
        return None
    return "ustunde" if price > level else "altinda"


def _rsi_zone(value: float | None) -> str | None:
    if value is None:
        return None
    if value >= config.RSI_OVERBOUGHT:
        return "asiri_alim"
    if value <= config.RSI_OVERSOLD:
        return "asiri_satim"
    return "notr"


def _range_contraction_pct(high: pd.Series, low: pd.Series, close: pd.Series) -> float | None:
    recent = range_pct(high, low, close, config.VCP_RECENT_RANGE_DAYS)
    baseline = range_pct(high, low, close, config.VCP_BASELINE_RANGE_DAYS)
    if recent is None or not baseline:
        return None
    return recent / baseline * 100.0


def _volume_contraction_pct(volume: pd.Series) -> float | None:
    recent = volume.tail(config.VCP_RECENT_VOLUME_DAYS).mean()
    baseline = volume.tail(config.VCP_BASELINE_VOLUME_DAYS).mean()
    if pd.isna(recent) or not baseline or pd.isna(baseline):
        return None
    return float(recent / baseline * 100.0)


def _volume_vs_avg_pct(volume: pd.Series) -> float | None:
    avg = last_value(volume_sma(volume, 20))
    last = last_value(volume)
    if avg is None or last is None or avg == 0:
        return None
    return (last / avg - 1.0) * 100.0


def _trend_sentence(
    ema21_rising: bool | None, ema50_rising: bool | None, weekly_aligned: bool | None
) -> str:
    if ema21_rising is None or ema50_rising is None:
        base = "Trend yönü için yeterli geçmiş veri yok."
    elif ema21_rising and ema50_rising:
        base = "Kısa ve orta vadeli trend yükselişte (EMA21 ve EMA50 yukarı eğimli)."
    elif not ema21_rising and not ema50_rising:
        base = "Trend aşağı yönlü (EMA21 ve EMA50 düşüş eğiminde)."
    else:
        base = "Trend karışık -- kısa ve orta vadeli EMA'lar farklı yönlerde."
    if weekly_aligned is True:
        base += " Haftalık trend de aynı yönü destekliyor."
    elif weekly_aligned is False:
        base += " Haftalık trend farklı yönde, dikkat."
    return base


def _momentum_sentence(rsi_value: float | None, zone: str | None) -> str:
    if rsi_value is None or zone is None:
        return "Momentum verisi için yeterli geçmiş yok."
    if zone == "asiri_alim":
        return f"Momentum aşırı alım bölgesinde (RSI {rsi_value:.0f})."
    if zone == "asiri_satim":
        return f"Momentum aşırı satım bölgesinde (RSI {rsi_value:.0f})."
    return f"Momentum nötr bölgede (RSI {rsi_value:.0f})."


def _volatility_sentence(range_c: float | None, volume_c: float | None) -> str:
    if range_c is None or volume_c is None:
        return "Volatilite/sıkışma verisi için yeterli geçmiş yok."
    tight_range = range_c <= config.VCP_RANGE_CONTRACTION_MAX_PCT
    tight_volume = volume_c <= config.VCP_VOLUME_CONTRACTION_MAX_PCT
    if tight_range and tight_volume:
        state = "sıkışma modunda"
    else:
        state = "normal aralıkta, belirgin bir sıkışma yok"
    return (
        f"Volatilite {state} (10g/40g range oranı %{range_c:.0f}, "
        f"10g/50g hacim oranı %{volume_c:.0f})."
    )


def _volume_sentence(vs_avg: float | None, obv: str, cmf_state: str) -> str:
    if vs_avg is None:
        vol_part = "Hacim verisi yetersiz."
    else:
        direction = "üstünde" if vs_avg >= 0 else "altında"
        vol_part = f"Hacim, 20 günlük ortalamasının %{abs(vs_avg):.0f} {direction}."
    obv_label = {"yukselis": "yükselişte", "dusus": "düşüşte", "yatay": "yatay"}[obv]
    cmf_label = {
        "accumulation": "birikim (accumulation) okuyor",
        "distribution": "dağıtım (distribution) okuyor",
        "notr": "nötr",
    }[cmf_state]
    return f"{vol_part} OBV {obv_label}, para akışı (CMF) {cmf_label}."


def _position_sentence(high52: float | None, low52: float | None) -> str:
    if high52 is None or low52 is None:
        return "52 haftalık aralık için yeterli veri yok."
    return f"52 haftalık zirveden %{high52:.1f}, dipten %{low52:.1f} uzaklıkta."


def _signals_sentence(long_groups: list[int], short_groups: list[int]) -> str:
    if not long_groups and not short_groups:
        return "Şu an My Trade taramasında (trade_scan) eşleşen sinyal yok."
    parts = []
    if long_groups:
        parts.append("LONG yönünde Grup " + ", ".join(str(g) for g in long_groups))
    if short_groups:
        parts.append("SHORT yönünde Grup " + ", ".join(str(g) for g in short_groups))
    return "My Trade taramasında eşleşiyor: " + "; ".join(parts) + "."


def score_symbol(symbol: str, df: pd.DataFrame) -> SymbolReport | None:
    """Pure per-symbol scoring against an already-fetched history. Split out
    from `build_report` the same way trade_scan.py/vcp_scan.py split their
    `scan_symbol` from the fetch, so tests can exercise this without a
    network call."""
    if df.empty:
        return None

    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    price = float(close.iloc[-1])
    change_1d = pct_change_last(close)

    ema21_rising = _ema_rising(close, 21)
    ema50_rising = _ema_rising(close, 50)
    sma50 = last_value(sma(close, config.SMA_FAST))
    sma200 = last_value(sma(close, config.SMA_SLOW))
    weekly_aligned = weekly_trend_up(close, config.WEEKLY_TREND_EMA)

    rsi_value = last_value(rsi_indicator(close, config.RSI_PERIOD))
    zone = _rsi_zone(rsi_value)
    stoch_k, stoch_d = stochastic_rsi(close, config.STOCH_RSI_PERIOD)
    smi, smi_signal = stochastic_momentum_index(
        high, low, close, config.SMI_PERIOD, config.SMI_SIGNAL, config.SMI_SIGNAL
    )

    atr14 = last_value(atr(high, low, close, config.ATR_PERIOD))
    adr = average_daily_range_pct(high, low, config.VCP_ADR_PERIOD)
    range_contraction = _range_contraction_pct(high, low, close)
    volume_contraction = _volume_contraction_pct(volume)

    vs_avg = _volume_vs_avg_pct(volume)
    obv = money_flow.obv_trend(on_balance_volume(close, volume))
    cmf = last_value(chaikin_money_flow(high, low, close, volume, config.CMF_PERIOD))
    cmf_state = money_flow.cmf_signal(cmf)
    mfi = last_value(money_flow_index(high, low, close, volume, config.MFI_PERIOD))

    high52 = pct_from_52w_high(close, config.WEEK_52_TRADING_DAYS)
    low52 = pct_from_52w_low(close, config.WEEK_52_TRADING_DAYS)

    trade_signals = trade_scan.scan_symbol(symbol, "-", df)
    long_groups = next((s.groups for s in trade_signals if s.direction == "long"), [])
    short_groups = next((s.groups for s in trade_signals if s.direction == "short"), [])

    summary_tr = " ".join(
        [
            _trend_sentence(ema21_rising, ema50_rising, weekly_aligned),
            _momentum_sentence(rsi_value, zone),
            _volatility_sentence(range_contraction, volume_contraction),
            _volume_sentence(vs_avg, obv, cmf_state),
            _position_sentence(high52, low52),
            _signals_sentence(long_groups, short_groups),
            "Bu bir tahmin değil, göstergelerin şu anki mekanik durumudur -- "
            "yatırım tavsiyesi değildir.",
        ]
    )

    return SymbolReport(
        symbol=symbol,
        price=price,
        change_1d=change_1d,
        ema21_rising=ema21_rising,
        ema50_rising=ema50_rising,
        price_vs_sma50=_price_vs_level(price, sma50),
        price_vs_sma200=_price_vs_level(price, sma200),
        weekly_trend_aligned=weekly_aligned,
        rsi=rsi_value,
        rsi_zone=zone,
        stoch_rsi_k=last_value(stoch_k),
        stoch_rsi_d=last_value(stoch_d),
        smi=last_value(smi),
        smi_signal=last_value(smi_signal),
        atr_14=atr14,
        adr_pct=adr,
        range_contraction_pct=range_contraction,
        volume_contraction_pct=volume_contraction,
        volume_vs_avg_pct=vs_avg,
        obv_trend=obv,
        cmf=cmf,
        cmf_signal=cmf_state,
        mfi=mfi,
        pct_from_52w_high=high52,
        pct_from_52w_low=low52,
        matched_long_groups=long_groups,
        matched_short_groups=short_groups,
        summary_tr=summary_tr,
    )


def build_report(symbol: str) -> SymbolReport | None:
    """Fetches history for one arbitrary symbol and scores it. None on
    empty history (bad/delisted ticker)."""
    df = data.get_history(symbol, period=config.DEFAULT_HISTORY_PERIOD)
    return score_symbol(symbol, df)
