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

export interface PortfolioSummary {
  totals: PortfolioTotals;
  alerts: Alert[];
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

export interface NewsItem {
  symbol: string;
  title: string;
  link: string;
  source: string;
  published: string;
}

export interface SeriesResult {
  key: string;
  label_tr: string;
  label_en: string;
  return_pct: number;
  series: { dates: string[]; values: (number | null)[] };
}

class ApiError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
  ) {
    super(`portfoy API ${path} responded ${status}`);
  }
}

async function apiGet<T>(path: string): Promise<T> {
  const base = process.env.PORTFOY_API_URL;
  const key = process.env.PORTFOY_API_KEY;
  if (!base || !key) {
    throw new Error("PORTFOY_API_URL / PORTFOY_API_KEY are not configured");
  }
  const res = await fetch(new URL(path, base), {
    headers: { "X-API-Key": key },
    cache: "no-store",
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
  return apiGet<MacroRow[]>("/api/market/macro");
}

export function getBreadth(): Promise<BreadthSnapshot | null> {
  return apiGet<BreadthSnapshot | null>("/api/market/breadth");
}

export function getSentiment(): Promise<SentimentScore | null> {
  return apiGet<SentimentScore | null>("/api/market/sentiment");
}

export function getRotation(includeMine = false): Promise<SectorRotation[]> {
  return apiGet<SectorRotation[]>(`/api/rotation?include_mine=${includeMine}`);
}

export function getCalendar(days = 45): Promise<MarketEvent[]> {
  return apiGet<MarketEvent[]>(`/api/calendar?days=${days}`);
}

export function getOptionsScan(): Promise<OptionActivity[]> {
  return apiGet<OptionActivity[]>("/api/options");
}

export function getNews(symbol: string, lang = "tr"): Promise<NewsItem[]> {
  return apiGet<NewsItem[]>(`/api/news/${encodeURIComponent(symbol)}?lang=${lang}`);
}

export function getCompare(period: string, base: "TRY" | "USD"): Promise<SeriesResult[]> {
  return apiGet<SeriesResult[]>(`/api/compare?period=${period}&base=${base}`);
}
