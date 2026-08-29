import "server-only";

export interface PositionMetrics {
  symbol: string;
  currency: "TRY" | "USD";
  quantity: number;
  avg_cost: number;
  price: number;
  change_pct: number;
  value: number;
  value_try: number;
  value_usd: number;
  pnl: number;
  pnl_pct: number;
  weight: number;
  rsi: number | null;
  sma_fast: number | null;
  sma_slow: number | null;
  atr_stop: number | null;
}

export interface CashHolding {
  currency: "TRY" | "USD";
  amount: number;
}

export interface PositionsPayload {
  metrics: PositionMetrics[];
  cash: CashHolding[];
  usdtry: number | null;
}

export interface PortfolioTotals {
  value_try: number;
  value_usd: number;
  invested_try: number;
  invested_usd: number;
  cash_try: number;
  cash_usd: number;
  cash_weight: number;
  cost_try: number;
  cost_usd: number;
  pnl_usd: number;
  pnl_pct: number;
  daily_pct: number;
}

export interface Alert {
  severity: "crit" | "warn" | "info";
  key: string;
  params: Record<string, string>;
}

export interface PositionHealth {
  symbol: string;
  score: number;
  reasons: string[];
  verdict: "zayifliyor" | "notr" | "guclu";
}

export interface PortfolioSummary {
  totals: PortfolioTotals;
  alerts: Alert[];
  position_health: PositionHealth[];
}

export interface MacroRow {
  symbol: string;
  label: string;
  price: number;
  change_pct: number;
}

export interface BreadthSnapshot {
  sample_size: number;
  pct_above_50: number;
  pct_above_200: number;
  advancers: number;
  decliners: number;
  new_high_20d: number;
  new_low_20d: number;
  trin: number | null;
  mcclellan: number | null;
}

export interface YieldCurveSnapshot {
  yield_10y: number | null;
  yield_3m: number | null;
  spread_10y_3m: number | null;
  inverted: boolean;
  credit_spread_proxy_change: number | null;
  credit_stress: boolean;
}

export interface AnalystView {
  target_mean: number | null;
  target_high: number | null;
  target_low: number | null;
  consensus: "al" | "tut" | "sat" | null;
  num_analysts: number | null;
}

export interface SentimentScore {
  composite: number;
  components: Record<string, number>;
}

export interface SectorRotation {
  symbol: string;
  label_tr: string;
  label_en: string;
  tail_x: number[];
  tail_y: number[];
  quadrant: "leading" | "weakening" | "lagging" | "improving";
  prev_quadrant: "leading" | "weakening" | "lagging" | "improving";
  perf_1w: number;
  perf_1m: number;
  perf_3m: number;
}

export interface SectorLeader {
  symbol: string;
  perf_1w: number;
  perf_1m: number;
  perf_3m: number;
}

export interface RotationPayload {
  sectors: SectorRotation[];
  leaders: Record<string, SectorLeader[]>;
  commentary: string | null;
}

export interface TradeSignal {
  symbol: string;
  sector: string;
  price: number;
  change_1d: number;
  direction: "long" | "short";
  groups: number[];
  atr_14: number | null;
  suggested_stop: number | null;
  pct_from_52w_high: number | null;
  pct_from_52w_low: number | null;
  weekly_trend_aligned: boolean | null;
}

export interface TradeScanPayload {
  signals: TradeSignal[];
}

export interface MoneyFlowSignal {
  symbol: string;
  sector: string;
  price: number;
  change_1d: number;
  cmf: number | null;
  cmf_signal: "accumulation" | "distribution" | "notr";
  mfi: number | null;
  obv_trend: "yukselis" | "dusus" | "yatay";
  institutional_pct: number | null;
  insider_net_pct_6m: number | null;
}

export interface MoneyFlowPayload {
  signals: MoneyFlowSignal[];
  commentary: string | null;
}

export interface FundamentalSnapshot {
  symbol: string;
  sector: string;
  pe: number | null;
  peg: number | null;
  ev_ebitda: number | null;
  revenue_growth: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  fcf_yield: number | null;
  verdict: "ucuz" | "makul" | "pahali" | "belirsiz";
}

export interface FundamentalScanPayload {
  signals: FundamentalSnapshot[];
}

export interface VcpCandidate {
  symbol: string;
  sector: string;
  price: number;
  change_1d: number;
  adr_pct: number;
  trailing_return_pct: number;
  range_contraction_pct: number;
  volume_contraction_pct: number;
  pct_from_52w_high: number;
  suggested_stop: number | null;
}

export interface VcpScanPayload {
  candidates: VcpCandidate[];
  commentary: string | null;
}

export interface TrendCandidate {
  symbol: string;
  sector: string;
  price: number;
  change_1d: number;
  direction: "boga" | "ayi";
  score: number;
  strength: "guclu" | "olusuyor" | "erken";
  ma_trend_confirmed: boolean;
  trendline_confirmed: boolean | null;
  structural_stop: number | null;
  volume_confirmed: boolean;
  money_flow_signal: "accumulation" | "distribution" | "notr";
  money_flow_aligned: boolean;
  adx: number | null;
  adx_rising: boolean | null;
  trend_maturity: "zayif" | "saglikli" | "tukenebilir" | "belirsiz";
  rsi_divergence_warning: boolean;
  trend_age_days: number;
  newly_triggered: boolean;
}

export interface TrendScanPayload {
  sectors: TrendCandidate[];
  stocks: TrendCandidate[];
  commentary: string | null;
}

export interface RotationOverlapCandidate {
  symbol: string;
  sector: string;
  perf_1m: number;
  signals: string[];
}

export interface RotationOverlapPayload {
  candidates: RotationOverlapCandidate[];
  commentary: string | null;
}

export interface FibLevel {
  ratio: number;
  price: number;
  kind: "retracement" | "extension";
  label: string;
}

export interface FibLevels {
  swing_high: number;
  swing_low: number;
  swing_high_date: string;
  swing_low_date: string;
  direction: "yukselis" | "dusus";
  lookback_days: number;
  levels: FibLevel[];
  nearest_ratio: number;
  nearest_price: number;
  pct_to_nearest: number;
  at_level: boolean;
  zone_label: string;
}

export interface SymbolReport {
  symbol: string;
  price: number;
  change_1d: number;
  currency: "TRY" | "USD";

  ema21_rising: boolean | null;
  ema50_rising: boolean | null;
  price_vs_sma50: "ustunde" | "altinda" | null;
  price_vs_sma200: "ustunde" | "altinda" | null;
  weekly_trend_aligned: boolean | null;

  rsi: number | null;
  rsi_zone: "asiri_alim" | "asiri_satim" | "notr" | null;
  stoch_rsi_k: number | null;
  stoch_rsi_d: number | null;
  smi: number | null;
  smi_signal: number | null;

  atr_14: number | null;
  adr_pct: number | null;
  range_contraction_pct: number | null;
  volume_contraction_pct: number | null;

  volume_vs_avg_pct: number | null;
  obv_trend: "yukselis" | "dusus" | "yatay";
  cmf: number | null;
  cmf_signal: "accumulation" | "distribution" | "notr";
  mfi: number | null;

  pct_from_52w_high: number | null;
  pct_from_52w_low: number | null;

  matched_long_groups: number[];
  matched_short_groups: number[];

  fib: FibLevels | null;

  summary_tr: string;
}

export interface SymbolContext {
  symbol: string;
  is_us: boolean;

  put_call_ratio: number | null;
  pcr_mood: "bearish" | "bullish" | "neutral" | null;
  option_expiry: string | null;
  call_volume: number | null;
  put_volume: number | null;

  institutional_pct: number | null;
  insider_net_pct_6m: number | null;

  unavailable_reason: "bist" | "no_data" | null;
}

export interface SymbolReportPayload {
  report: SymbolReport | null;
  context: SymbolContext | null;
  commentary: string | null;
}

export interface MarketPulse {
  commentary: string | null;
}

export interface MarketEvent {
  when: string;
  kind: "fomc" | "nfp" | "earnings";
  symbol: string;
}

export interface OptionActivity {
  symbol: string;
  expiry: string;
  call_volume: number;
  put_volume: number;
  call_oi: number;
  put_oi: number;
  top_contracts: Array<{
    type: "CALL" | "PUT";
    strike: number;
    last: number;
    volume: number;
    oi: number;
    iv: number;
  }>;
}

export interface Mover {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number | null;
  avg_volume_3m: number | null;
  relative_volume: number | null;
  sector: string | null;
  signals: TradeSignal[];
  news: NewsItem[];
}

export interface MoversScan {
  generated_at: string;
  gainers: Mover[];
  volume_spikes: Mover[];
  commentary: string | null;
}

export interface NewsItem {
  symbol: string;
  title: string;
  link: string;
  source: string;
  published: string;
  sentiment: "positive" | "negative" | "neutral";
  interpretation: string;
}

export interface SeriesResult {
  key: string;
  label_tr: string;
  label_en: string;
  return_pct: number;
  series: { dates: string[]; values: (number | null)[] };
}

export interface AddPositionInput {
  symbol: string;
  quantity: number;
  avg_cost: number;
  notes?: string;
}

class ApiError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
  ) {
    super(`portfoy API ${path} responded ${status}`);
  }
}

export class ApiMutationError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(`portfoy API ${path} responded ${status}`);
  }
}

/**
 * `revalidateSeconds` mirrors the *backend's own* cache TTL (see portfoy/
 * config.py) for market-wide/reference data -- the Python API is never
 * fresher than that anyway, so caching the same window at the Next.js fetch
 * layer costs no real freshness but skips a round trip + function
 * invocation on repeat navigation. Omit it (stays `no-store`) for anything
 * showing the user's own live P&L, where an extra caching layer on top of
 * the backend's own TTL would compound staleness.
 */
async function apiGet<T>(path: string, revalidateSeconds?: number): Promise<T> {
  const base = process.env.PORTFOY_API_URL;
  const key = process.env.PORTFOY_API_KEY;
  if (!base || !key) {
    throw new Error("PORTFOY_API_URL / PORTFOY_API_KEY are not configured");
  }
  const res = await fetch(new URL(path, base), {
    headers: { "X-API-Key": key },
    ...(revalidateSeconds
      ? { next: { revalidate: revalidateSeconds } }
      : { cache: "no-store" as const }),
  });
  if (!res.ok) {
    throw new ApiError(path, res.status);
  }
  return res.json() as Promise<T>;
}

export function getPositions(): Promise<PositionsPayload> {
  return apiGet<PositionsPayload>("/api/positions");
}

export function getPortfolioSummary(): Promise<PortfolioSummary> {
  return apiGet<PortfolioSummary>("/api/portfolio/summary");
}

export function getMacro(): Promise<MacroRow[]> {
  return apiGet<MacroRow[]>("/api/market/macro", 300);
}

export function getBreadth(): Promise<BreadthSnapshot | null> {
  return apiGet<BreadthSnapshot | null>("/api/market/breadth", 1800);
}

export function getSentiment(): Promise<SentimentScore | null> {
  return apiGet<SentimentScore | null>("/api/market/sentiment", 300);
}

export function getYieldCurve(): Promise<YieldCurveSnapshot> {
  return apiGet<YieldCurveSnapshot>("/api/market/yield-curve", 1800);
}

// Same 1800s window as breadth/yield-curve -- market_pulse_payload just
// narrates those same cached reads, so it can't be fresher than they are.
export function getMarketPulse(): Promise<MarketPulse> {
  return apiGet<MarketPulse>("/api/market/pulse", 1800);
}

export function getAnalystViews(): Promise<Record<string, AnalystView>> {
  return apiGet<Record<string, AnalystView>>("/api/analyst", 21600);
}

export function getRotation(includeMine = false): Promise<RotationPayload> {
  return apiGet<RotationPayload>(`/api/rotation?include_mine=${includeMine}`, 3600);
}

// No revalidateSeconds: this is triggered on demand by a button, not
// rendered at page-load, so every click should get a fresh scan.
export function getTradeScan(): Promise<TradeScanPayload> {
  return apiGet<TradeScanPayload>("/api/trade-scan");
}

export function getMoneyFlow(): Promise<MoneyFlowPayload> {
  return apiGet<MoneyFlowPayload>("/api/money-flow");
}

// No revalidateSeconds: same on-demand-scan pattern as trade scan/money flow
// -- per-symbol Yahoo quote-summary reads are too slow to run on every page
// load across the whole universe, so this is button-triggered.
export function getFundamentals(): Promise<FundamentalScanPayload> {
  return apiGet<FundamentalScanPayload>("/api/fundamentals");
}

// No revalidateSeconds: same on-demand-scan pattern as trade scan/money flow.
export function getVcpScan(): Promise<VcpScanPayload> {
  return apiGet<VcpScanPayload>("/api/vcp-scan");
}

// No revalidateSeconds: runs rotation + all three My Trade scans server-side
// on every call (money_flow's per-symbol ownership reads are slow), so this
// is button-triggered like the other My Trade panels, not page-load.
export function getRotationOverlap(): Promise<RotationOverlapPayload> {
  return apiGet<RotationOverlapPayload>("/api/rotation-overlap");
}

// No revalidateSeconds: same on-demand-scan pattern as VCP/trade-scan --
// full-universe 1y history fetch + swing-point detection per symbol is too
// slow to run on every page load, so this is button-triggered.
export function getTrendScan(): Promise<TrendScanPayload> {
  return apiGet<TrendScanPayload>("/api/trend-scan");
}

export function getCalendar(days = 45): Promise<MarketEvent[]> {
  return apiGet<MarketEvent[]>(`/api/calendar?days=${days}`, 3600);
}

export function getOptionsScan(): Promise<OptionActivity[]> {
  return apiGet<OptionActivity[]>("/api/options", 900);
}

export function getNews(symbol: string, lang = "tr"): Promise<NewsItem[]> {
  return apiGet<NewsItem[]>(`/api/news/${encodeURIComponent(symbol)}?lang=${lang}`, 900);
}

// No revalidateSeconds -- on-demand, one symbol at a time, same pattern as
// getTradeScan/getVcpScan.
export function getSymbolReport(symbol: string): Promise<SymbolReportPayload> {
  return apiGet<SymbolReportPayload>(`/api/report/${encodeURIComponent(symbol)}`);
}

// The backend itself only refreshes every ~20min (see the movers-scan cron
// workflow), so caching this window at the fetch layer costs no real
// freshness -- just skips a round trip on repeat navigation.
export function getMovers(): Promise<MoversScan> {
  return apiGet<MoversScan>("/api/movers", 300);
}

export function getCompare(period: string, base: "TRY" | "USD"): Promise<SeriesResult[]> {
  return apiGet<SeriesResult[]>(`/api/compare?period=${period}&base=${base}`, 900);
}

async function apiMutate<T>(path: string, init: RequestInit): Promise<T> {
  const base = process.env.PORTFOY_API_URL;
  const key = process.env.PORTFOY_API_KEY;
  if (!base || !key) {
    throw new Error("PORTFOY_API_URL / PORTFOY_API_KEY are not configured");
  }
  const res = await fetch(new URL(path, base), {
    ...init,
    headers: { "X-API-Key": key, "Content-Type": "application/json" },
    cache: "no-store",
  });
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiMutationError(path, res.status, body);
  }
  return body as T;
}

export function addPosition(input: AddPositionInput): Promise<PositionsPayload> {
  return apiMutate<PositionsPayload>("/api/positions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function removePosition(symbol: string): Promise<PositionsPayload> {
  return apiMutate<PositionsPayload>(`/api/positions/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}
