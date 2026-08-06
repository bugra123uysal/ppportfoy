import type { PositionMetrics } from "@/lib/api";
import { fmtMoney } from "@/lib/format";
import { CATEGORICAL_PALETTE, OTHER_SLOT_COLOR } from "@/lib/palette";

const MAX_SLOTS = 7;
// Not part of the categorical palette on purpose -- cash is liquidity, not a
// holding, so it borrows the app's accent color instead of the next slot.
const CASH_COLOR = "#ffb020";

const SIZE = 200;
const STROKE = 24;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

interface Slice {
  key: string;
  weight: number;
  valueUsd: number;
  color: string;
}

function buildSlices(
  metrics: PositionMetrics[],
  cashWeight: number,
  cashValueUsd: number,
): Slice[] {
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

  if (cashWeight > 0) {
    slices.push({ key: "Nakit", weight: cashWeight, valueUsd: cashValueUsd, color: CASH_COLOR });
  }

  return slices.filter((s) => s.weight > 0);
}

export function AllocationPie({
  metrics,
  cashWeight,
  cashValueUsd,
  totalValueTry,
  positionCount,
}: {
  metrics: PositionMetrics[];
  cashWeight: number;
  cashValueUsd: number;
  totalValueTry: number;
  positionCount: number;
}) {
  if (metrics.length === 0 && cashWeight === 0) {
    return <p className="text-sm text-text-faint">Pozisyon yok.</p>;
  }

  const slices = buildSlices(metrics, cashWeight, cashValueUsd);

  const { arcs } = slices.reduce<{
    cumulative: number;
    arcs: Array<Slice & { dash: number; offset: number }>;
  }>(
    (state, slice) => ({
      cumulative: state.cumulative + slice.weight,
      arcs: [
        ...state.arcs,
        { ...slice, dash: slice.weight * CIRCUMFERENCE, offset: -state.cumulative * CIRCUMFERENCE },
      ],
    }),
    { cumulative: 0, arcs: [] },
  );

  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
      <div className="chart-pop relative shrink-0" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="var(--surface-2)"
            strokeWidth={STROKE}
          />
          {arcs.map((arc) => (
            <circle
              key={arc.key}
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={arc.color}
              strokeWidth={STROKE}
              strokeDasharray={`${arc.dash} ${CIRCUMFERENCE - arc.dash}`}
              strokeDashoffset={arc.offset}
              transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
            >
              <title>
                {`${arc.key}: %${(arc.weight * 100).toFixed(1)} · ${fmtMoney(arc.valueUsd, "USD")}`}
              </title>
            </circle>
          ))}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="tabular text-lg font-semibold text-text">
            {fmtMoney(totalValueTry, "TRY")}
          </p>
          <p className="text-xs text-text-faint">{positionCount} pozisyon</p>
        </div>
      </div>

      <div className="flex flex-col gap-2 self-center">
        {slices.map((slice) => (
          <div key={slice.key} className="flex items-center gap-2 text-xs">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
              style={{ backgroundColor: slice.color }}
            />
            <span className="w-14 shrink-0 text-text">{slice.key}</span>
            <span className="tabular text-text-faint">
              %{(slice.weight * 100).toFixed(1)} · {fmtMoney(slice.valueUsd, "USD")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
