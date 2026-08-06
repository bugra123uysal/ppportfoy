import type { PositionHealth } from "@/lib/api";
import { Panel } from "@/components/panel";

const VERDICT_LABEL: Record<PositionHealth["verdict"], string> = {
  zayifliyor: "Zayıflıyor",
  notr: "Nötr",
  guclu: "Güçlü",
};

const VERDICT_CLASS: Record<PositionHealth["verdict"], string> = {
  zayifliyor: "bg-neg-soft text-neg",
  notr: "bg-surface-2 text-text-dim",
  guclu: "bg-pos-soft text-pos",
};

const VERDICT_RANK: Record<PositionHealth["verdict"], number> = {
  zayifliyor: 0,
  notr: 1,
  guclu: 2,
};

export function PositionHealthPanel({ health }: { health: PositionHealth[] }) {
  if (health.length === 0) {
    return null;
  }

  const sorted = [...health].sort((a, b) => VERDICT_RANK[a.verdict] - VERDICT_RANK[b.verdict]);

  return (
    <Panel
      title="Pozisyon Sağlığı"
      subtitle="Elindeki her pozisyona teknik sinyal + sermaye akışı + fundamental değerleme uygulanır — bir sat/al sinyali değil, mekanik bir özet"
    >
      <div className="flex flex-col gap-3">
        {sorted.map((h) => (
          <div
            key={h.symbol}
            className="flex flex-col gap-1.5 border-b border-border/60 pb-3 last:border-0 last:pb-0"
          >
            <div className="flex items-center gap-3">
              <span className="font-medium text-text">{h.symbol}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_CLASS[h.verdict]}`}
              >
                {VERDICT_LABEL[h.verdict]}
              </span>
            </div>
            {h.reasons.length > 0 && (
              <ul className="flex flex-col gap-0.5 pl-1 text-xs text-text-faint">
                {h.reasons.map((reason, i) => (
                  <li key={i}>· {reason}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}
