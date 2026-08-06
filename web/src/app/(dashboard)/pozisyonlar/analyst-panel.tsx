import type { AnalystView, PositionMetrics } from "@/lib/api";
import { Panel } from "@/components/panel";
import { fmtMoney, fmtPct } from "@/lib/format";

const CONSENSUS_LABEL: Record<NonNullable<AnalystView["consensus"]>, string> = {
  al: "Al",
  tut: "Tut",
  sat: "Sat",
};

const CONSENSUS_CLASS: Record<NonNullable<AnalystView["consensus"]>, string> = {
  al: "bg-pos-soft text-pos",
  tut: "bg-surface-2 text-text-dim",
  sat: "bg-neg-soft text-neg",
};

export function AnalystPanel({
  metrics,
  views,
}: {
  metrics: PositionMetrics[];
  views: Record<string, AnalystView>;
}) {
  const rows = metrics.filter((m) => views[m.symbol]);
  if (rows.length === 0) {
    return null;
  }

  return (
    <Panel
      title="Analist Görüşleri"
      subtitle="Hedef fiyat ve konsensüs (Yahoo Finance, ABD hisseleri) — yatırım tavsiyesi değildir"
    >
      <div className="flex flex-col gap-3">
        {rows.map((m) => {
          const view = views[m.symbol];
          const upside =
            view.target_mean !== null ? (view.target_mean / m.price - 1.0) * 100.0 : null;
          return (
            <div
              key={m.symbol}
              className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3 last:border-0 last:pb-0"
            >
              <div className="flex items-center gap-3">
                <span className="font-medium text-text">{m.symbol}</span>
                {view.consensus && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${CONSENSUS_CLASS[view.consensus]}`}
                  >
                    {CONSENSUS_LABEL[view.consensus]}
                  </span>
                )}
                {view.num_analysts !== null && (
                  <span className="text-xs text-text-faint">{view.num_analysts} analist</span>
                )}
              </div>
              <div className="text-right">
                <p className="tabular text-sm text-text">
                  {view.target_mean !== null ? fmtMoney(view.target_mean, "USD") : "—"}
                  <span className="ml-1.5 text-xs text-text-faint">hedef</span>
                </p>
                {upside !== null && (
                  <p className={`tabular text-xs ${upside >= 0 ? "text-pos" : "text-neg"}`}>
                    {fmtPct(upside)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
