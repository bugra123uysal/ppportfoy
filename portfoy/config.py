"""Application-wide constants. No secrets live here (or anywhere in the repo)."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "Portföy Takip Merkezi"

# --- Storage ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
HISTORY_FILE = DATA_DIR / "history.json"
MAX_POSITIONS = 100
MAX_HISTORY_DAYS = 1825  # ~5 years of daily snapshots

# --- Data fetching ---------------------------------------------------------
QUOTE_CACHE_TTL = 300        # seconds
HISTORY_CACHE_TTL = 900
NEWS_CACHE_TTL = 900
REQUEST_TIMEOUT = 10         # seconds, for every outbound HTTP request
DEFAULT_HISTORY_PERIOD = "1y"

FX_USDTRY = "TRY=X"

# Macro context tickers shown on the overview strip.
MACRO_TICKERS = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "XU100.IS": "BIST 100",
    "^VIX": "VIX",
    "DX-Y.NYB": "DXY",
    "^TNX": "US 10Y",
    "TRY=X": "USD/TRY",
    "GC=F": "Altın",
    "BZ=F": "Brent",
    "BTC-USD": "Bitcoin",
}

# --- Risk / alert thresholds ----------------------------------------------
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
SMA_FAST = 50
SMA_SLOW = 200
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
DAILY_DROP_WARN = -4.0       # % single-day fall that deserves attention
DAILY_DROP_CRIT = -8.0
LOSS_WARN_PCT = -10.0        # % below your average cost
LOSS_CRIT_PCT = -20.0
CONCENTRATION_WARN = 0.35    # one position > 35% of the portfolio
VIX_WARN = 25.0
VIX_CRIT = 32.0
EARNINGS_SOON_DAYS = 7

# --- Hisse Raporu: Fibonacci -----------------------------------------------
# Retracement/extension levels off the highest High / lowest Low in the
# trailing window -- see portfoy/fibonacci.py. 120 sessions (~6 months) is
# long enough to catch a real swing without drifting into stale, no-longer-
# relevant price history.
FIB_LOOKBACK_DAYS = 120
FIB_RETRACEMENT_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXTENSION_RATIOS = (1.272, 1.618)
FIB_NEAR_LEVEL_PCT = 1.5     # within this % of a level counts as "at" it

# --- Hisse Raporu: range/hacim daralması (volatility contraction) ----------
# Qullamaggie/Minervini tarzı "sıkışıyor mu" okuması -- range_contraction_pct/
# volume_contraction_pct/adr_pct alanları, portfoy/report.py.
VCP_ADR_PERIOD = 20
VCP_RECENT_RANGE_DAYS = 10
# Not "önceki 40 gün" (hariç) -- son 40 günün range'i, son 10 günü de kapsar
# (ikisi de bugüne çıpalı .tail() penceresi). Kısa pencere uzun pencerenin
# alt kümesi olduğu için kısa/uzun oranı yapısal olarak <=100 -- amaç dışlamak
# değil, "son birkaç gün, son bir buçuk ayın tipik salınımına göre ne kadar
# sıkıştı" sorusunu ölçmek.
VCP_BASELINE_RANGE_DAYS = 40
VCP_RANGE_CONTRACTION_MAX_PCT = 60.0       # son 10g range, son 40g range'in en fazla bu yüzdesi
VCP_RECENT_VOLUME_DAYS = 10
VCP_BASELINE_VOLUME_DAYS = 50              # aynı çıpalı-pencere mantığı -- yukarıdaki notu bkz.
VCP_VOLUME_CONTRACTION_MAX_PCT = 70.0      # son 10g ort. hacim, son 50g ort.nın en fazla bu %'si

# --- Options radar ---------------------------------------------------------
# Most liquid US option names; the user's own US holdings are added on top.
# BIST stocks have no option chains on Yahoo, so only US symbols are scanned.
OPTIONS_UNIVERSE = (
    "SPY", "QQQ", "NVDA", "TSLA", "AAPL", "AMD", "MSFT", "AMZN",
    "META", "GOOGL", "PLTR", "NFLX", "COIN", "IWM", "MU", "AVGO",
)
OPTIONS_CACHE_TTL = 900          # options data is 15-min delayed on Yahoo anyway
OPTIONS_TOP_CONTRACTS = 8        # most-traded contracts shown in the detail table
PCR_BEARISH = 1.0                # put/call ratio above this = hedging/bearish tilt
PCR_BULLISH = 0.7                # below this = call-heavy speculation

# --- Market compass: breadth ----------------------------------------------
# A 60-name large-cap sample across all 11 sectors. Breadth from a sample
# tracks index-wide breadth closely and keeps the batch download fast/free.
BREADTH_UNIVERSE = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK-B", "JPM",
    "V", "MA", "UNH", "LLY", "XOM", "CVX", "HD", "PG", "KO", "PEP",
    "COST", "WMT", "MRK", "ABBV", "ORCL", "CRM", "AMD", "NFLX", "INTC", "QCOM",
    "TXN", "CSCO", "ADBE", "BA", "CAT", "GE", "HON", "MMM", "UPS", "RTX",
    "GS", "MS", "BAC", "WFC", "C", "BLK", "T", "VZ", "CMCSA", "DIS",
    "NKE", "MCD", "SBUX", "LOW", "PFE", "TMO", "ABT", "LIN", "NEE", "DUK",
)
BREADTH_CACHE_TTL = 1800
BREADTH_HEALTHY = 60.0       # % above 200d SMA considered a solid foundation
BREADTH_WEAK = 40.0

# --- Market compass: sentiment score ---------------------------------------
SENT_VIX_CALM = 10.0         # VIX at/below this scores 100 (max greed)
SENT_VIX_PANIC = 40.0        # VIX at/above this scores 0 (max fear)
SENT_PCR_FEAR = 1.5          # SPY put/call at/above this scores 0
SENT_PCR_GREED = 0.5         # at/below this scores 100
SENT_MOMENTUM_SMA = 125      # S&P vs its ~6-month average

# --- Market compass: yield curve / credit spread ----------------------------
# NY Fed's own recession-probability model uses the 3-month/10-year spread
# (not the more commonly cited 2s10s) -- both tickers are standard CBOE
# treasury-yield indices on Yahoo, quoted directly in percent.
YIELD_10Y_TICKER = "^TNX"
YIELD_3M_TICKER = "^IRX"
# HYG (high-yield corp) vs LQD (investment-grade corp): both are corporate
# bond ETFs of similar duration profile, so their ratio isolates credit-risk
# pricing better than HY-vs-Treasury would (which conflates credit and
# pure interest-rate/duration risk).
CREDIT_HY_TICKER = "HYG"
CREDIT_IG_TICKER = "LQD"
CREDIT_SPREAD_LOOKBACK = 20      # trading sessions (~1 month)
CREDIT_STRESS_THRESHOLD = -3.0  # % ratio decline over the lookback flagged as stress
YIELD_CURVE_CACHE_TTL = 1800

# --- Market compass: economic calendar -------------------------------------
# Official FOMC schedule (published by the Federal Reserve a year ahead).
# Dates are the DECISION day (second day of the two-day meeting).
FOMC_DATES_2026 = (
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
)
CALENDAR_LOOKAHEAD_DAYS = 45

# --- News ------------------------------------------------------------------
NEWS_PER_SYMBOL = 8
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# --- Sector rotation (RRG) -------------------------------------------------
# The 11 SPDR sector ETFs, measured against SPY.
SECTOR_ETFS = {
    "XLK": ("Teknoloji", "Technology"),
    "XLF": ("Finans", "Financials"),
    "XLE": ("Enerji", "Energy"),
    "XLV": ("Sağlık", "Health Care"),
    "XLY": ("İsteğe Bağlı Tüketim", "Cons. Discretionary"),
    "XLP": ("Temel Tüketim", "Cons. Staples"),
    "XLI": ("Sanayi", "Industrials"),
    "XLB": ("Hammadde", "Materials"),
    "XLU": ("Kamu Hizmetleri", "Utilities"),
    "XLRE": ("Gayrimenkul", "Real Estate"),
    "XLC": ("İletişim", "Communication"),
}
RRG_BENCHMARK = "SPY"
RRG_PERIOD = "3y"            # weekly bars are resampled from this window
RRG_RATIO_WINDOW = 10        # weeks of relative performance behind RS-Ratio
RRG_MOMENTUM_WINDOW = 10     # weeks, SMA used to detect acceleration
RRG_TAIL_WEEKS = 8           # how many weeks of trail to draw behind the arrow
RRG_CLIP = 3.0               # cap scores at ±3σ so one wild symbol can't squash the map

# Curated pool of liquid, well-known large caps per sector -- NOT an
# exhaustive constituent list. "Top 5" leaders are picked from within this
# pool by trailing 1-month return, so results are only as good as this pool.
SECTOR_LEADER_STOCKS: dict[str, tuple[str, ...]] = {
    "XLK": ("AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "ADBE"),
    "XLF": ("JPM", "V", "MA", "GS", "MS", "BAC", "WFC", "BLK"),
    "XLE": ("XOM", "CVX", "COP", "SLB", "EOG", "WMB"),
    "XLV": ("UNH", "LLY", "JNJ", "MRK", "ABBV", "TMO", "ABT", "PFE"),
    "XLY": ("AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "BKNG"),
    "XLP": ("PG", "KO", "PEP", "COST", "WMT", "PM"),
    "XLI": ("GE", "CAT", "RTX", "HON", "UNP", "BA", "UPS", "DE"),
    "XLB": ("LIN", "SHW", "APD", "ECL", "FCX", "NEM"),
    "XLU": ("NEE", "SO", "DUK", "AEP", "SRE", "D"),
    "XLRE": ("PLD", "AMT", "EQIX", "SPG", "PSA", "O"),
    "XLC": ("GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ"),
}
SECTOR_LEADERS_TOP_N = 5

# --- Indicator screener (trade_scan.py) -------------------------------
# Thresholds below are standard TA convention, not backtested. Applied
# per-symbol only (report.py, position_health.py) -- see that module's
# module docstring.
WEEK_52_TRADING_DAYS = 252
WEEKLY_TREND_EMA = 10           # weeks, for the multi-timeframe confirmation filter
SMI_PERIOD, SMI_SIGNAL = 10, 3
BB_PERIOD, BB_STD = 20, 2.0
MAD_OVERSOLD_PCT = -5.0        # close this far below its own 21d EMA = "aşırı ucuz" dip
MAD_OVERBOUGHT_PCT = 5.0       # close this far above its own 21d EMA (downtrend) = overbought rally
STOCH_RSI_PERIOD = 14
UT_BOT_ATR_PERIOD, UT_BOT_KEY_VALUE = 10, 2.0   # QuantNomad's public defaults
TREND_MAGIC_CCI_PERIOD = 20
STOP_ATR_MULT = 1.5           # suggested stop = last close - ATR14 * this

# Group 4: TradingView's built-in "Median" indicator (hl2 median vs its own
# EMA, same length -- default length 3) confirming a Stochastic RSI value
# crossing its own added EMA (14d, per the source notes).
MEDIAN_PERIOD = 3
GROUP4_RSI_EMA_PERIOD = 14

# --- Sermaye akışı (money_flow.py) ------------------------------------
# Combines a daily price/volume-derived signal (CMF/MFI/OBV, free from
# OHLCV) with a periodic filing-derived one (institutional %/insider net
# buying, free from Yahoo's Holders tab). Applied per-symbol only (report.py,
# position_health.py).
OWNERSHIP_CACHE_TTL = 21600     # holders/insider filings update slowly; 6h is plenty fresh
CMF_PERIOD = 20
CMF_THRESHOLD = 0.05            # |CMF| below this counts as "nötr", not accumulation/distribution
MFI_PERIOD = 14
OBV_TREND_LOOKBACK = 10         # bars compared to call OBV "yükseliş"/"düşüş"/"yatay"

# --- Fundamental değerleme (fundamentals.py) --------------------------
# Valuation/quality/growth metrics from Yahoo's quote summary (yfinance's
# Ticker.info), classified by position_health.py against the user's own
# holdings. Updates quarterly at most, so it shares money_flow's
# ownership/analyst cache cadence.
FUNDAMENTALS_CACHE_TTL = 21600
FUNDAMENTALS_PEG_CHEAP = 1.0        # PEG below this reads as undervalued relative to growth
FUNDAMENTALS_PEG_EXPENSIVE = 2.0    # PEG above this reads as expensive relative to growth
FUNDAMENTALS_EV_EBITDA_CHEAP = 10.0     # capital-structure-neutral valuation, low = attractive
FUNDAMENTALS_EV_EBITDA_EXPENSIVE = 15.0

# --- Evre Takibi: Weinstein 4 evre analizi ----------------------------------
# Stan Weinstein'ın 30 haftalık hareketli ortalama + eğimine dayalı evre
# sınıflandırması, portföydeki her pozisyona uygulanır (bkz.
# portfoy/stage_analysis.py). Bir tarama değil -- sadece elde olan hisseler.
STAGE_ANALYSIS_PERIOD = "3y"        # günlük veri; haftalığa örneklenir (30h SMA için yeterli)
STAGE_SMA_WEEKS = 30
STAGE_SLOPE_LOOKBACK_WEEKS = 4      # SMA eğimi bu kadar hafta öncesine göre ölçülür
STAGE_CONTEXT_LOOKBACK_WEEKS = 20   # SMA yatayken Evre 1 mi Evre 3 mü olduğunu ayırt etmek için
STAGE_FLAT_THRESHOLD_PCT = 1.0      # SMA değişimi bu aralıktaysa "yatay" sayılır
STAGE_RS_LOOKBACK_WEEKS = 10        # göreli güç (RS) trendi bu kadar hafta öncesine göre ölçülür
STAGE_BENCHMARKS = {"USD": "^GSPC", "TRY": "XU100.IS"}

# --- Risk & Uyarılar: pozisyon sağlığı --------------------------------------
# Applies the same technical/money-flow/fundamental reads My Trade's scanners
# use to the user's own holdings instead of the fixed sector-leader universe
# -- see portfoy/position_health.py. Thresholds on the combined score below.
POSITION_HEALTH_WEAKENING = -2
POSITION_HEALTH_STRONG = 2

# --- Cash ------------------------------------------------------------------
CASH_CURRENCIES = ("TRY", "USD")
MAX_CASH = 1e12

# --- Benchmark comparison --------------------------------------------------
# Everything is converted to one base currency before being compared, so a
# TRY-denominated index and a USD-denominated one stay apples-to-apples.
BENCHMARKS = {
    "^GSPC": ("S&P 500", "S&P 500", "USD"),
    "^IXIC": ("Nasdaq", "Nasdaq", "USD"),
    "XU100.IS": ("BIST 100", "BIST 100", "TRY"),
    "GC=F": ("Altın", "Gold", "USD"),
    "TRY=X": ("Dolar (USD/TRY)", "US Dollar", "TRY"),
    "BTC-USD": ("Bitcoin", "Bitcoin", "USD"),
}
COMPARE_PERIODS = {
    "per_1m": 21,
    "per_3m": 63,
    "per_6m": 126,
    "per_ytd": None,     # start of the calendar year
    "per_1y": 252,
}
DEFAULT_COMPARE_PERIOD = "per_3m"
COMPARE_HISTORY_PERIOD = "2y"
# --- Nemotron AI commentary --------------------------------------------
# Free NIM API (build.nvidia.com), OpenAI-compatible -- see
# portfoy/commentary.py's module docstring for the full design. Requires an
# NVIDIA_API_KEY env var; every caller degrades to no commentary without it.
NEMOTRON_API_BASE = "https://integrate.api.nvidia.com/v1"
NEMOTRON_SUPER_MODEL = "nvidia/nemotron-3-super-120b-a12b"  # most panels
NEMOTRON_ULTRA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"  # Hisse Raporu only
NEMOTRON_TIMEOUT = 20  # seconds -- LLM calls run well past REQUEST_TIMEOUT

ROTATION_CACHE_TTL = 3600    # seconds; weekly data barely moves intraday
