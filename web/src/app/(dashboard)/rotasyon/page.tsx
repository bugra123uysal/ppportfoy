import Link from "next/link";
import { getRotation } from "@/lib/api";
import { Panel } from "@/components/panel";
import { RrgChart } from "@/components/rrg-chart";
import { fmtPct } from "@/lib/format";

const QUADRANT_TR: Record<string, string> = {
  leading: "Lider",
  weakening: "Zayıflayan",
  lagging: "Geride",
  improving: "İyileşen",
};

export default async function RotationPage({
  searchParams,
}: {
  searchParams: Promise<{ mine?: string }>;
}) {
  const { mine } = await searchParams;
  const includeMine = mine === "1";
  const points = await getRotation(includeMine);
  const movers = points.filter((p) => p.quadrant !== p.prev_quadrant);

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Sektör Rotasyonu</h1>
        <p className="mt-1 text-sm text-text-faint">
          Relative Rotation Graph (RRG) — sektörler SPY&apos;a göre, kendi aralarında skorlanır.
        </p>
      </div>

      <Link
        href={includeMine ? "/rotasyon" : "/rotasyon?mine=1"}
        className={`w-fit rounded-full border px-3 py-1.5 text-xs transition-colors ${
          includeMine
            ? "border-accent bg-accent-soft text-accent"
            : "border-border text-text-dim hover:border-border-strong hover:text-text"
        }`}
      >
        {includeMine ? "✓ Holdinglerim gösteriliyor" : "Holdinglerimi de göster"}
      </Link>

      {points.length === 0 ? (
        <p className="text-sm text-text-faint">Veri alınamadı.</p>
      ) : (
        <>
          <Panel title="RRG Haritası">
            <RrgChart points={points} />
          </Panel>

          {movers.length > 0 && (
            <Panel title="Kadran Değişimleri">
              <ul className="flex flex-col gap-1.5 text-sm">
                {movers.map((p) => (
                  <li key={p.symbol} className="text-text-dim">
                    <span className="font-medium text-text">{p.symbol}</span> ({p.label_tr}):{" "}
                    {QUADRANT_TR[p.prev_quadrant]} → {QUADRANT_TR[p.quadrant]}
                  </li>
                ))}
              </ul>
            </Panel>
          )}

          <Panel title="Performans Sıralaması">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-text-faint">
                    <th className="py-2 pr-4 font-medium">Sektör</th>
                    <th className="py-2 pr-4 font-medium">Bölge</th>
                    <th className="py-2 pr-4 text-right font-medium">1H</th>
                    <th className="py-2 pr-4 text-right font-medium">1A</th>
                    <th className="py-2 text-right font-medium">3A</th>
                  </tr>
                </thead>
                <tbody>
                  {[...points]
                    .sort((a, b) => b.perf_1m - a.perf_1m)
                    .map((p) => (
                      <tr key={p.symbol} className="border-b border-border/60 last:border-0">
                        <td className="py-2.5 pr-4 font-medium text-text">
                          {p.symbol} <span className="text-text-faint">· {p.label_tr}</span>
                        </td>
                        <td className="py-2.5 pr-4 text-text-dim">{QUADRANT_TR[p.quadrant]}</td>
                        <PerfCell value={p.perf_1w} />
                        <PerfCell value={p.perf_1m} />
                        <PerfCell value={p.perf_3m} last />
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </>
  );
}

function PerfCell({ value, last }: { value: number; last?: boolean }) {
  return (
    <td
      className={`tabular py-2.5 text-right ${last ? "" : "pr-4"} ${value >= 0 ? "text-pos" : "text-neg"}`}
    >
      {fmtPct(value, 1)}
    </td>
  );
}
