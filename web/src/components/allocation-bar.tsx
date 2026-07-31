import type { PositionMetrics } from "@/lib/api";
import { fmtMoney } from "@/lib/format";
import { CATEGORICAL_PALETTE, OTHER_SLOT_COLOR } from "@/lib/palette";

const MAX_SLOTS = 7;

interface Slice {
  key: string;
  weight: number;
  valueUsd: number;
  color: string;
}

function buildSlices(metrics: PositionMetrics[]): Slice[] {
  const sorted = [...metrics].sort((a, b) => b.weight - a.weight);
  const head = sorted.slice(0, MAX_SLOTS);
  const tail = sorted.slice(MAX_SLOTS);

  const slices: Slice[] = head.map((m, i) => ({
    key: m.symbol,
    weight: m.weight,
    valueUsd: m.value_usd,
    color: CATEGORICAL_PALETTE[i],
  }));

  if (tail.length > 0) {
    slices.push({
      key: "Diğer",
      weight: tail.reduce((sum, m) => sum + m.weight, 0),
      valueUsd: tail.reduce((sum, m) => sum + m.value_usd, 0),
      color: OTHER_SLOT_COLOR,
    });
  }
  return slices.filter((s) => s.weight > 0);
}

export function AllocationBar({ metrics }: { metrics: PositionMetrics[] }) {
  if (metrics.length === 0) {
    return <p className="text-sm text-text-faint">Pozisyon yok.</p>;
  }
  const slices = buildSlices(metrics);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex h-6 gap-[2px] overflow-hidden rounded-md bg-surface">
        {slices.map((slice) => (
          <div
            key={slice.key}
            style={{ flexGrow: slice.weight, backgroundColor: slice.color }}
            className="h-full first:rounded-l-sm last:rounded-r-sm"
            title={`${slice.key}: %${(slice.weight * 100).toFixed(1)}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {slices.map((slice) => (
          <div key={slice.key} className="flex items-center gap-2 text-xs">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
              style={{ backgroundColor: slice.color }}
            />
            <span className="text-text">{slice.key}</span>
            <span className="tabular text-text-faint">
              %{(slice.weight * 100).toFixed(1)} · {fmtMoney(slice.valueUsd, "USD")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
