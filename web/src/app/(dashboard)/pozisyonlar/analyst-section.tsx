import { getAnalystViews } from "@/lib/api";
import type { PositionMetrics } from "@/lib/api";
import { AnalystPanel } from "./analyst-panel";

// Split from PositionsOverview so the (cached, but still an extra hop)
// analyst fetch never holds up the core holdings view -- `metrics` comes in
// as a prop from the already-resolved positions fetch, so this never
// re-requests /api/positions on its own.
export async function AnalystSection({ metrics }: { metrics: PositionMetrics[] }) {
  const views = await getAnalystViews();
  return <AnalystPanel metrics={metrics} views={views} />;
}
