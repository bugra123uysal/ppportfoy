"""Trend Bulucu -- market yapısı (Dow Theory swing HH/HL) + MA rejimi +
trendline teyidinden oluşan 3 katmanlı mekanik trend taraması, artı beş
bağımsız teyit/bağlam sinyali (hacim, para akışı, ADX olgunluğu, RSI
diverjansı, trend yaşı).

"Trend Nasıl Yakalanır?" videosunun (bkz. proje hafızası) üç bölümüne bire
bir karşılık gelir:

  1. Market Yapısı  -- boğa trendi = ardışık yükselen tepe (HH) + yükselen dip
     (HL); ayı trendi = ardışık alçalan tepe (LH) + alçalan dip (LL). Bu katman
     SERT bir filtredir: yapı net değilse (konsolidasyon/karışık), sembol
     "trendde" sayılmaz ve sonuca hiç girmez.
  2. MA Rejimi -- fiyatın ve hızlı EMA'nın yavaş SMA'ya göre konumu (Golden/
     Death Cross rejimi). Skora katkı verir, filtre değildir.
  3. Trendline -- son swing noktalarından geçen regresyon çizgisinin eğimi ve
     fiyatın çizginin doğru tarafında olup olmadığı. Skora katkı verir.

Skor 1-3 arası: yalnız Katman 1 = 1 ("erken"), + bir teyit daha = 2
("oluşuyor"), üç katman da uyumlu = 3 ("güçlü").

Bunun üzerine, skoru DEĞİŞTİRMEYEN beş bağımsız bağlam sinyali eklenir --
skor "yapı ne kadar net" sorusuna cevap verirken, bunlar "bu trende ne kadar
güvenilir/taze" sorusuna cevap verir, ayrı bir eksen olarak gösterilir:

  - Hacim teyidi     -- son günlerin hacmi 20 günlük ortalamayı geçmiş mi
                        (bir kırılımın düşük hacimle olması az inanç demektir).
  - Para akışı uyumu -- money_flow.py'nin CMF sinyali trend yönüyle çelişmiyor
                        mu (aynı modülün mantığını, ayrı bir tarama yapmadan
                        reuse eder).
  - ADX + olgunluk   -- ADX trend gücünü ölçer; yüksek ADX + dönmeye başlaması
                        genelde trendin en olgun/tükenmiş noktasıdır (erken
                        giriş, ADX henüz 25'i yeni geçmişken aranır).
  - RSI diverjansı   -- fiyat yeni bir HH/LL yaparken RSI aynı yönde teyit
                        etmiyorsa (tersine), trendin iç gücü zayıflıyor
                        olabilir -- erken tükenme uyarısı.
  - Trend yaşı       -- yapıyı onaylayan son bacak kaç bardır sürüyor (en
                        yakın HL'den önceki swing dipten -- boğada -- bugüne
                        kadarki mesafe). Kısa yaş = "yeni tetiklenmiş" trend.

Aynı fonksiyon hem hisse evrenine (SECTOR_LEADER_STOCKS) hem sektör
ETF'lerine (SECTOR_ETFS) uygulanır -- bkz. api_data.py'deki
trend_scan_payload -- "hangi sektör trendde" ile "hangi hisse trendde" aynı
tanımı paylaşsın diye.

Bu mekanik bir kural taraması, yatırım tavsiyesi değildir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config, data
from .indicators import (
    adx,
    chaikin_money_flow,
    ema,
    pct_change_last,
    rsi,
    sma,
    swing_highs,
    swing_lows,
    volume_sma,
)
from .money_flow import cmf_signal

BOGA = "boga"
AYI = "ayi"

_STRENGTH_BY_SCORE = {1: "erken", 2: "olusuyor", 3: "guclu"}


@dataclass(frozen=True)
class TrendCandidate:
    symbol: str
    sector: str
    price: float
    change_1d: float
    direction: str                    # "boga" | "ayi"
    score: int                        # 1..3 (Katman 1-2-3: yapı + MA + trendline)
    strength: str                     # "erken" | "olusuyor" | "guclu"
    ma_trend_confirmed: bool          # Katman 2
    trendline_confirmed: bool | None  # Katman 3
    structural_stop: float | None
    volume_confirmed: bool            # son günlerin hacmi 20g ortalamanın üstünde mi
    money_flow_signal: str            # "accumulation" | "distribution" | "notr"
    money_flow_aligned: bool          # sinyal trend yönüyle çelişmiyor mu
    adx: float | None
    adx_rising: bool | None
    trend_maturity: str               # "zayif" | "saglikli" | "tukenebilir" | "belirsiz"
    rsi_divergence_warning: bool      # fiyat/RSI diverjansı -- erken tükenme uyarısı
    trend_age_days: int               # onaylayan bacak kaç bardır sürüyor
    newly_triggered: bool             # trend_age_days <= TREND_FRESH_MAX_AGE_DAYS


def _classify_structure(swing_high_px: np.ndarray, swing_low_px: np.ndarray) -> str | None:
    """Son iki teyitli swing tepe ve son iki teyitli swing dibi karşılaştırır
    -- "son pivot bir öncekini kırdı mı" sorusunun cevabı, Dow Theory market
    yapısının minimum kanıtı. Yetersiz veri ya da karışık sinyal (biri
    yükseliyor biri düşüyor) -> None, yani "net bir yapı yok"."""
    if len(swing_high_px) < 2 or len(swing_low_px) < 2:
        return None
    higher_high = swing_high_px[-1] > swing_high_px[-2]
    higher_low = swing_low_px[-1] > swing_low_px[-2]
    if higher_high and higher_low:
        return BOGA
    if not higher_high and not higher_low:
        return AYI
    return None


def _ma_trend_confirmed(direction: str, price: float, ma_fast: float, ma_slow: float) -> bool:
    """Golden Cross rejimi (boğa): fiyat + hızlı EMA, yavaş SMA'nın üstünde.
    Death Cross rejimi (ayı): ikisi de altında."""
    if direction == BOGA:
        return price > ma_slow and ma_fast > ma_slow
    return price < ma_slow and ma_fast < ma_slow


def _trendline_confirmed(
    direction: str,
    positions: np.ndarray,
    prices: np.ndarray,
    last_position: int,
    last_price: float,
) -> bool | None:
    """Son swing noktalarından geçen regresyon çizgisi doğru yönde eğimli mi
    ve fiyat çizginin (henüz) kırılmamış tarafında mı. Boğa için son swing
    dipleri (yükselen destek), ayı için son swing tepeleri (alçalan direnç)
    kullanılır -- videonun "Trend Destek ve Direnç Çizgileri" bölümü."""
    if len(positions) < 2:
        return None
    slope, intercept = np.polyfit(positions, prices, 1)
    projected = slope * last_position + intercept
    if direction == BOGA:
        return bool(slope > 0 and last_price >= projected)
    return bool(slope < 0 and last_price <= projected)


def _volume_confirmed(volume: pd.Series) -> bool:
    """Son TREND_VOLUME_RECENT_DAYS günün ortalama hacmi, 20 günlük
    ortalamayı geçiyor mu -- düşük hacimli bir kırılım az inançla sürer."""
    vol_avg = volume_sma(volume, config.TREND_VOLUME_SMA_PERIOD)
    if pd.isna(vol_avg.iloc[-1]):
        return False
    recent_avg = volume.tail(config.TREND_VOLUME_RECENT_DAYS).mean()
    return bool(recent_avg > vol_avg.iloc[-1])


def _money_flow_alignment(
    direction: str, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
) -> tuple[str, bool]:
    """money_flow.py'nin CMF sinyalini (yeni bir tarama yapmadan) reuse eder
    -- para akışı trend yönüyle çelişmiyor mu."""
    cmf = chaikin_money_flow(high, low, close, volume, config.CMF_PERIOD)
    cmf_last = None if cmf.empty or pd.isna(cmf.iloc[-1]) else float(cmf.iloc[-1])
    signal = cmf_signal(cmf_last)
    if direction == BOGA:
        aligned = signal != "distribution"
    else:
        aligned = signal != "accumulation"
    return signal, aligned


def _trend_maturity(adx_value: float | None, adx_rising: bool | None) -> str:
    """Araştırma: yüksek ADX + dönmeye başlaması genelde trendin en olgun/
    tükenmiş noktasıdır -- en iyi giriş ADX henüz eşiği yeni geçmişken."""
    if adx_value is None or adx_rising is None:
        return "belirsiz"
    if adx_value >= config.TREND_ADX_MATURE_THRESHOLD and not adx_rising:
        return "tukenebilir"
    if adx_value < config.TREND_ADX_TREND_THRESHOLD:
        return "zayif"
    return "saglikli"


def _rsi_divergence(
    direction: str,
    rsi_series: pd.Series,
    swing_high_pos: np.ndarray,
    swing_high_px: np.ndarray,
    swing_low_pos: np.ndarray,
    swing_low_px: np.ndarray,
) -> bool:
    """Bearish diverjans (boğa): fiyat yeni HH yapıyor ama RSI o tepelerde
    alçalıyor -- iç güç zayıflıyor. Bullish diverjans (ayı): fiyat yeni LL
    yapıyor ama RSI o diplerde yükseliyor. İkisi de erken tükenme uyarısı."""
    rsi_values = rsi_series.to_numpy()
    if direction == BOGA:
        if len(swing_high_pos) < 2:
            return False
        r1, r2 = rsi_values[swing_high_pos[-2]], rsi_values[swing_high_pos[-1]]
        if pd.isna(r1) or pd.isna(r2):
            return False
        return bool(swing_high_px[-1] > swing_high_px[-2] and r2 < r1)
    if len(swing_low_pos) < 2:
        return False
    r1, r2 = rsi_values[swing_low_pos[-2]], rsi_values[swing_low_pos[-1]]
    if pd.isna(r1) or pd.isna(r2):
        return False
    return bool(swing_low_px[-1] < swing_low_px[-2] and r2 > r1)


def scan_symbol(symbol: str, sector: str, df: pd.DataFrame) -> TrendCandidate | None:
    """The part of `build_trend_scan` that doesn't fetch -- pure per-symbol
    scoring against an already-fetched history, same split as
    trade_scan.py/money_flow.py/vcp_scan.py's scan_symbol()."""
    min_bars = config.TREND_MA_SLOW + config.TREND_SWING_WINDOW * 2 + 1
    if df.empty or len(df) < min_bars:
        return None

    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]
    positions = np.arange(len(df))

    high_mask = swing_highs(high, config.TREND_SWING_WINDOW).to_numpy()
    low_mask = swing_lows(low, config.TREND_SWING_WINDOW).to_numpy()
    swing_high_pos, swing_high_px = positions[high_mask], high.to_numpy()[high_mask]
    swing_low_pos, swing_low_px = positions[low_mask], low.to_numpy()[low_mask]

    direction = _classify_structure(swing_high_px, swing_low_px)
    if direction is None:
        return None

    ma_fast = ema(close, config.TREND_MA_FAST)
    ma_slow = sma(close, config.TREND_MA_SLOW)
    if pd.isna(ma_fast.iloc[-1]) or pd.isna(ma_slow.iloc[-1]):
        return None
    last_close = float(close.iloc[-1])
    ma_confirmed = _ma_trend_confirmed(
        direction, last_close, float(ma_fast.iloc[-1]), float(ma_slow.iloc[-1])
    )

    if direction == BOGA:
        line_pos, line_px = swing_low_pos, swing_low_px
        structural_stop = float(swing_low_px[-1])
        trend_age_days = int(positions[-1] - swing_low_pos[-2])
    else:
        line_pos, line_px = swing_high_pos, swing_high_px
        structural_stop = float(swing_high_px[-1])
        trend_age_days = int(positions[-1] - swing_high_pos[-2])

    points = config.TREND_TRENDLINE_POINTS
    trendline_confirmed = _trendline_confirmed(
        direction, line_pos[-points:], line_px[-points:], int(positions[-1]), last_close
    )
    score = 1 + int(ma_confirmed) + int(bool(trendline_confirmed))

    volume_confirmed = _volume_confirmed(volume)
    money_flow_signal, money_flow_aligned = _money_flow_alignment(
        direction, high, low, close, volume
    )

    adx_line, _plus_di, _minus_di = adx(high, low, close, config.ATR_PERIOD)
    lookback = config.TREND_ADX_RISING_LOOKBACK
    adx_value = None if pd.isna(adx_line.iloc[-1]) else float(adx_line.iloc[-1])
    adx_rising = (
        None
        if adx_value is None or len(adx_line) <= lookback or pd.isna(adx_line.iloc[-1 - lookback])
        else bool(adx_line.iloc[-1] > adx_line.iloc[-1 - lookback])
    )

    rsi_series = rsi(close, config.RSI_PERIOD)
    rsi_divergence_warning = _rsi_divergence(
        direction, rsi_series, swing_high_pos, swing_high_px, swing_low_pos, swing_low_px
    )

    return TrendCandidate(
        symbol=symbol,
        sector=sector,
        price=last_close,
        change_1d=pct_change_last(close),
        direction=direction,
        score=score,
        strength=_STRENGTH_BY_SCORE[score],
        ma_trend_confirmed=ma_confirmed,
        trendline_confirmed=trendline_confirmed,
        structural_stop=round(structural_stop, 2),
        volume_confirmed=volume_confirmed,
        money_flow_signal=money_flow_signal,
        money_flow_aligned=money_flow_aligned,
        adx=round(adx_value, 1) if adx_value is not None else None,
        adx_rising=adx_rising,
        trend_maturity=_trend_maturity(adx_value, adx_rising),
        rsi_divergence_warning=rsi_divergence_warning,
        trend_age_days=trend_age_days,
        newly_triggered=trend_age_days <= config.TREND_FRESH_MAX_AGE_DAYS,
    )


def build_trend_scan(universe: dict[str, str]) -> list[TrendCandidate]:
    """Scan `universe` (ticker -> sector/label) for trend candidates, ranked
    strongest-first (score desc, then trailing 1-day move desc)."""
    histories = data.get_histories(tuple(universe), period=config.TREND_HISTORY_PERIOD)
    results: list[TrendCandidate] = []
    for symbol, sector in universe.items():
        candidate = scan_symbol(symbol, sector, histories.get(symbol, pd.DataFrame()))
        if candidate is not None:
            results.append(candidate)
    return sorted(results, key=lambda c: (-c.score, -c.change_1d))
