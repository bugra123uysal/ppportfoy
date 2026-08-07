"""VCP (Volatility Contraction Pattern) breakout adayları -- "gece taraması".

Qullamaggie/Minervini tarzı momentum tarama metodolojisinin "patlamaya
hazır aday havuzu" yarısı: büyük hareketler rastgele gelmez, belirli bir
teknik yapıdan çıkar. Patlamadan önce hisse şöyle görünür (kaynak: kullanıcı
ekran görüntüsü, bkz. config.py'deki VCP_* eşikleri):

  1. Son ~3 ayda büyük bir yükseliş yapmış (öncü rally -- "güçlü mover").
  2. Şu an tight consolidation'da -- son günlerin fiyat aralığı, önceki
     döneme göre daralmış (range contraction).
  3. Hacim kuruyor -- son günlerin ortalama hacmi, önceki döneme göre
     düşmüş (satıcı bitiyor demek).
  4. Fiyat 10 ve 20 günlük EMA'nın üstünde.
  5. 52 haftalık zirveye yakın.

Bu modül yalnızca "gece taraması"nı yapar: hangi isimler bu beş kriteri de
karşılıyor. Gün içi gerçek zamanlı kırılım teyidi (Setup B / Episodic Pivot)
kapsam dışı -- bkz. movers.py'nin hacim öncüllüğü taraması, kavramsal olarak
en yakın parça.

Aynı SECTOR_LEADER_STOCKS evrenini kullanır (trade_scan.py, money_flow.py,
fundamentals.py ile aynı desen). Bu metodoloji orijinalde küçük/orta
ölçekli, yüksek beta'lı isimlerde taranır -- büyük ölçekli bu evrende
ADR eşiğini geçen aday sayısı az/değişken olabilir, bu evrenin doğal sınırı,
taramanın hatası değil.

Bu mekanik bir kural taraması, yatırım tavsiyesi değildir.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, data
from .indicators import (
    atr,
    average_daily_range_pct,
    ema,
    pct_change_last,
    pct_change_over,
    pct_from_52w_high,
    range_pct,
)


@dataclass(frozen=True)
class VcpCandidate:
    symbol: str
    sector: str
    price: float
    change_1d: float
    adr_pct: float                  # ortalama günlük range % -- yüksek = daha "hareketli" isim
    trailing_return_pct: float      # ~3 aylık öncü rally
    range_contraction_pct: float    # son 10g range / son 40g range * 100; düşük = daha sıkı
    volume_contraction_pct: float   # son 10g ort. hacim / son 50g ort. * 100; düşük = daha kuru
    pct_from_52w_high: float        # <=0; 0 = tam zirvede
    suggested_stop: float | None    # price - ATR14*STOP_ATR_MULT


def scan_symbol(symbol: str, sector: str, df: pd.DataFrame) -> VcpCandidate | None:
    """The part of `build_vcp_scan` that doesn't fetch -- pure per-symbol
    scoring against an already-fetched history, same split as trade_scan.py
    and money_flow.py's scan_symbol()."""
    min_bars = (
        max(
            config.VCP_BASELINE_RANGE_DAYS,
            config.VCP_BASELINE_VOLUME_DAYS,
            config.VCP_TRAILING_RETURN_LOOKBACK_DAYS,
        )
        + 1
    )
    if df.empty or len(df) < min_bars:
        return None

    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    adr = average_daily_range_pct(high, low, config.VCP_ADR_PERIOD)
    if adr is None or adr < config.VCP_ADR_MIN_PCT:
        return None

    trailing_return = pct_change_over(close, config.VCP_TRAILING_RETURN_LOOKBACK_DAYS)
    if trailing_return is None or trailing_return < config.VCP_TRAILING_RETURN_MIN_PCT:
        return None

    recent_range = range_pct(high, low, close, config.VCP_RECENT_RANGE_DAYS)
    baseline_range = range_pct(high, low, close, config.VCP_BASELINE_RANGE_DAYS)
    if recent_range is None or not baseline_range:
        return None
    range_contraction = recent_range / baseline_range * 100.0
    if range_contraction > config.VCP_RANGE_CONTRACTION_MAX_PCT:
        return None

    recent_vol = volume.tail(config.VCP_RECENT_VOLUME_DAYS).mean()
    baseline_vol = volume.tail(config.VCP_BASELINE_VOLUME_DAYS).mean()
    if pd.isna(recent_vol) or not baseline_vol or pd.isna(baseline_vol):
        return None
    volume_contraction = float(recent_vol / baseline_vol * 100.0)
    if volume_contraction > config.VCP_VOLUME_CONTRACTION_MAX_PCT:
        return None

    ema_fast = ema(close, config.VCP_EMA_FAST)
    ema_slow = ema(close, config.VCP_EMA_SLOW)
    if pd.isna(ema_fast.iloc[-1]) or pd.isna(ema_slow.iloc[-1]):
        return None
    last_close = float(close.iloc[-1])
    if not (last_close > float(ema_fast.iloc[-1]) and last_close > float(ema_slow.iloc[-1])):
        return None

    high52 = pct_from_52w_high(close, config.WEEK_52_TRADING_DAYS)
    if high52 is None or high52 < config.VCP_NEAR_52W_HIGH_MAX_PCT:
        return None

    atr14 = atr(high, low, close, config.ATR_PERIOD)
    atr_last = None if atr14.empty or pd.isna(atr14.iloc[-1]) else float(atr14.iloc[-1])
    suggested_stop = (
        round(last_close - atr_last * config.STOP_ATR_MULT, 2) if atr_last is not None else None
    )

    return VcpCandidate(
        symbol=symbol,
        sector=sector,
        price=last_close,
        change_1d=pct_change_last(close),
        adr_pct=round(adr, 2),
        trailing_return_pct=round(trailing_return, 1),
        range_contraction_pct=round(range_contraction, 1),
        volume_contraction_pct=round(volume_contraction, 1),
        pct_from_52w_high=round(high52, 1),
        suggested_stop=suggested_stop,
    )


def build_vcp_scan(universe: dict[str, str]) -> list[VcpCandidate]:
    """Scan `universe` (ticker -> sector label) for VCP breakout candidates."""
    histories = data.get_histories(tuple(universe), period=config.VCP_HISTORY_PERIOD)
    results: list[VcpCandidate] = []
    for symbol, sector in universe.items():
        candidate = scan_symbol(symbol, sector, histories.get(symbol, pd.DataFrame()))
        if candidate is not None:
            results.append(candidate)
    return results
