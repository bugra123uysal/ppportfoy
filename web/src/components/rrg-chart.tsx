import type { SectorRotation } from "@/lib/api";

const WIDTH = 700;
const HEIGHT = 560;
const PAD = 40;

export const QUADRANT_COLOR: Record<SectorRotation["quadrant"], string> = {
  leading: "var(--pos)",
  weakening: "var(--accent)",
  improving: "#3987e5",
  lagging: "var(--neg)",
};

const QUADRANT_FILL: Record<SectorRotation["quadrant"], string> = {
  leading: "var(--pos-soft)",
  weakening: "var(--accent-soft)",
  improving: "rgba(57,135,229,0.08)",
  lagging: "var(--neg-soft)",
};

export function RrgChart({ points }: { points: SectorRotation[] }) {
  if (points.length === 0) {
    return <p className="text-sm text-text-faint">Veri yok.</p>;
  }

  const allX = points.flatMap((p) => p.tail_x);
  const allY = points.flatMap((p) => p.tail_y);
  const span = Math.max(
    Math.max(...allX.map((x) => Math.abs(x - 100))),
    Math.max(...allY.map((y) => Math.abs(y - 100))),
    3,
  ) * 1.15;

  const plot = Math.min(WIDTH, HEIGHT) - PAD * 2;
  const sx = (x: number) => WIDTH / 2 + ((x - 100) / span) * (plot / 2);
  const sy = (y: number) => HEIGHT / 2 - ((y - 100) / span) * (plot / 2);

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Sektör rotasyonu RRG grafiği">
      {/* quadrant backgrounds */}
      <rect x={WIDTH / 2} y={0} width={WIDTH / 2} height={HEIGHT / 2} fill={QUADRANT_FILL.leading} />
      <rect x={WIDTH / 2} y={HEIGHT / 2} width={WIDTH / 2} height={HEIGHT / 2} fill={QUADRANT_FILL.weakening} />
      <rect x={0} y={0} width={WIDTH / 2} height={HEIGHT / 2} fill={QUADRANT_FILL.improving} />
      <rect x={0} y={HEIGHT / 2} width={WIDTH / 2} height={HEIGHT / 2} fill={QUADRANT_FILL.lagging} />

      <line x1={WIDTH / 2} x2={WIDTH / 2} y1={0} y2={HEIGHT} stroke="var(--border-strong)" strokeWidth={1} />
      <line x1={0} x2={WIDTH} y1={HEIGHT / 2} y2={HEIGHT / 2} stroke="var(--border-strong)" strokeWidth={1} />

      <text x={WIDTH - 8} y={16} textAnchor="end" fontSize={11} fill="var(--text-faint)">Lider</text>
      <text x={WIDTH - 8} y={HEIGHT - 8} textAnchor="end" fontSize={11} fill="var(--text-faint)">Zayıflayan</text>
      <text x={8} y={16} fontSize={11} fill="var(--text-faint)">İyileşen</text>
      <text x={8} y={HEIGHT - 8} fontSize={11} fill="var(--text-faint)">Geride</text>

      {points.map((p) => {
        const color = QUADRANT_COLOR[p.quadrant];
        const path = p.tail_x
          .map((x, i) => `${i === 0 ? "M" : "L"} ${sx(x)} ${sy(p.tail_y[i])}`)
          .join(" ");
        const cx = sx(p.tail_x[p.tail_x.length - 1]);
        const cy = sy(p.tail_y[p.tail_y.length - 1]);
        return (
          <g key={p.symbol}>
            <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeOpacity={0.5} />
            <circle cx={cx} cy={cy} r={5} fill={color} stroke="var(--surface)" strokeWidth={2} />
            <text x={cx + 8} y={cy + 4} fontSize={11} fill="var(--text)">
              {p.symbol}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
