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

# --- My Trade: indicator screener -------------------------------------
# Reuses SECTOR_LEADER_STOCKS (flattened, ticker -> sector) as the scan
# universe, so results carry a sector label for free. Thresholds below are
# standard TA convention, not backtested -- see portfoy/trade_scan.py.
TRADE_SCAN_HISTORY_PERIOD = "6mo"
TRADE_SCAN_CACHE_TTL = 3600
SMI_PERIOD, SMI_SIGNAL = 10, 3
BB_PERIOD, BB_STD = 20, 2.0
MAD_OVERSOLD_PCT = -5.0        # close this far below its own 21d EMA = "aşırı ucuz" dip
STOCH_RSI_PERIOD = 14
UT_BOT_ATR_PERIOD, UT_BOT_KEY_VALUE = 10, 2.0   # QuantNomad's public defaults
TREND_MAGIC_CCI_PERIOD = 20
STOP_ATR_MULT = 1.5           # suggested stop = last close - ATR14 * this

# --- My Trade: sermaye akışı (money flow) ----------------------------------
# Same scan universe as the indicator screener above. Combines a daily
# price/volume-derived signal (CMF/MFI/OBV, free from OHLCV) with a periodic
# filing-derived one (institutional %/insider net buying, free from Yahoo's
# Holders tab) -- see portfoy/money_flow.py.
MONEY_FLOW_HISTORY_PERIOD = "6mo"
MONEY_FLOW_CACHE_TTL = 3600
OWNERSHIP_CACHE_TTL = 21600     # holders/insider filings update slowly; 6h is plenty fresh
CMF_PERIOD = 20
CMF_THRESHOLD = 0.05            # |CMF| below this counts as "nötr", not accumulation/distribution
MFI_PERIOD = 14
OBV_TREND_LOOKBACK = 10         # bars compared to call OBV "yükseliş"/"düşüş"/"yatay"

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
ROTATION_CACHE_TTL = 3600    # seconds; weekly data barely moves intraday
