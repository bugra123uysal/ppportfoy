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

export interface SectorLeader {
  symbol: string;
  perf_1w: number;
  perf_1m: number;
  perf_3m: number;
}

export interface RotationPayload {
  sectors: SectorRotation[];
  leaders: Record<string, SectorLeader[]>;
}

export interface TradeSignal {
  symbol: string;
  sector: string;
  price: number;
  change_1d: number;
  groups: number[];
  atr_14: number | null;
  suggested_stop: number | null;
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

export function getCalendar(days = 45): Promise<MarketEvent[]> {
  return apiGet<MarketEvent[]>(`/api/calendar?days=${days}`, 3600);
}

export function getOptionsScan(): Promise<OptionActivity[]> {
  return apiGet<OptionActivity[]>("/api/options", 900);
}

export function getNews(symbol: string, lang = "tr"): Promise<NewsItem[]> {
  return apiGet<NewsItem[]>(`/api/news/${encodeURIComponent(symbol)}?lang=${lang}`, 900);
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
