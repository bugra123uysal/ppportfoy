export interface ChartSeries {
  key: string;
  points: { x: number; y: number }[];
  emphasis?: boolean;
}

const WIDTH = 800;
const HEIGHT = 320;
const PAD = { top: 16, right: 16, bottom: 24, left: 44 };

export function LineChart({ series }: { series: ChartSeries[] }) {
  const allPoints = series.flatMap((s) => s.points);
  if (allPoints.length === 0) {
    return <p className="text-sm text-text-faint">Veri yok.</p>;
  }

  const xMin = Math.min(...allPoints.map((p) => p.x));
  const xMax = Math.max(...allPoints.map((p) => p.x));
  const yMin = Math.min(...allPoints.map((p) => p.y));
  const yMax = Math.max(...allPoints.map((p) => p.y));
  const yPad = (yMax - yMin) * 0.08 || 1;
  const yLo = yMin - yPad;
  const yHi = yMax + yPad;

  const plotW = WIDTH - PAD.left - PAD.right;
  const plotH = HEIGHT - PAD.top - PAD.bottom;
  const sx = (x: number) => PAD.left + ((x - xMin) / (xMax - xMin || 1)) * plotW;
  const sy = (y: number) => PAD.top + plotH - ((y - yLo) / (yHi - yLo || 1)) * plotH;

  const gridValues = [yLo, (yLo + yHi) / 2, yHi];

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Getiri karşılaştırma grafiği">
      {gridValues.map((v) => (
        <g key={v}>
          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={sy(v)}
            y2={sy(v)}
            stroke="var(--border)"
            strokeWidth={1}
          />
          <text x={4} y={sy(v) + 4} fontSize={10} fill="var(--text-faint)">
            {v.toFixed(0)}
          </text>
        </g>
      ))}
      {series
        .slice()
        .sort((a, b) => Number(a.emphasis ?? false) - Number(b.emphasis ?? false))
        .map((s) => {
          const d = s.points
            .map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.x)} ${sy(p.y)}`)
            .join(" ");
          const last = s.points[s.points.length - 1];
          return (
            <g key={s.key}>
              <path
                d={d}
                fill="none"
                stroke={s.emphasis ? "var(--accent)" : "var(--text-faint)"}
                strokeWidth={s.emphasis ? 2.5 : 1.5}
                strokeOpacity={s.emphasis ? 1 : 0.55}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              <circle
                cx={sx(last.x)}
                cy={sy(last.y)}
                r={s.emphasis ? 4.5 : 3}
                fill={s.emphasis ? "var(--accent)" : "var(--text-faint)"}
                stroke="var(--surface)"
                strokeWidth={2}
              />
            </g>
          );
        })}
    </svg>
  );
}
