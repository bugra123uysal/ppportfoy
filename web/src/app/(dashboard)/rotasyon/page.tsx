import Link from "next/link";
import { getRotation } from "@/lib/api";
import type { SectorLeader, SectorRotation } from "@/lib/api";
import { Panel } from "@/components/panel";
import { RrgChart } from "@/components/rrg-chart";
import { fmtPct } from "@/lib/format";

const QUADRANT_TR: Record<string, string> = {
  leading: "Lider",
  weakening: "Zayıflayan",
  lagging: "Geride",
  improving: "İyileşen",
};

// RRG heuristic: improving/leading sectors are still gaining relative
// strength, so they're the rotation candidates worth a look; weakening/
// lagging sectors are the ones to be rotating out of.
const ROTATE_IN_QUADRANTS = new Set(["leading", "improving"]);

function currentY(p: SectorRotation): number {
  return p.tail_y[p.tail_y.length - 1];
}

export default async function RotationPage({
  searchParams,
}: {
  searchParams: Promise<{ mine?: string }>;
}) {
  const { mine } = await searchParams;
  const includeMine = mine === "1";
  const { sectors: points, leaders } = await getRotation(includeMine);
  const movers = points.filter((p) => p.quadrant !== p.prev_quadrant);
  const candidates = points
    .filter((p) => ROTATE_IN_QUADRANTS.has(p.quadrant))
    .sort((a, b) => currentY(b) - currentY(a));
  const topPick = candidates[0];
  const runnerUps = candidates.slice(1, 3);

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
          <Panel title="Rotasyon Önerisi">
            {topPick ? (
              <div className="flex flex-col gap-2">
                <p className="text-sm text-text">
                  Şu an en güçlü konumda: {" "}
                  <span className="font-medium text-text">
                    {topPick.symbol} · {topPick.label_tr}
                  </span>{" "}
                  <span className="text-text-dim">({QUADRANT_TR[topPick.quadrant]} kadran)</span>{" "}
                  — son 1 ayda{" "}
                  <span className={topPick.perf_1m >= 0 ? "text-pos" : "text-neg"}>
                    {fmtPct(topPick.perf_1m, 1)}
                  </span>
                  .
                </p>
                {runnerUps.length > 0 && (
                  <p className="text-xs text-text-faint">
                    Diğer güçlü adaylar:{" "}
                    {runnerUps
                      .map((p) => `${p.symbol} (${QUADRANT_TR[p.quadrant]})`)
                      .join(", ")}
                  </p>
                )}
                <p className="text-[11px] text-text-faint">
                  Lider/iyileşen kadrandaki, momentumu en güçlü sektör baz alınarak
                  hesaplanmıştır. Yatırım tavsiyesi değildir.
                </p>
              </div>
            ) : (
              <p className="text-sm text-text-faint">
                Şu anda öne çıkan bir rotasyon adayı yok — tüm sektörler zayıflıyor ya da geride.
              </p>
            )}
          </Panel>

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

          <Panel title="Sektör Başına En İyi 5 Hisse" subtitle="Son 1 ay getirisine göre sıralı">
            <SectorLeaders sectors={points} leaders={leaders} />
          </Panel>

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

function SectorLeaders({
  sectors,
  leaders,
}: {
  sectors: SectorRotation[];
  leaders: Record<string, SectorLeader[]>;
}) {
  const withLeaders = sectors.filter((s) => (leaders[s.symbol] ?? []).length > 0);
  if (withLeaders.length === 0) {
    return <p className="text-sm text-text-faint">Veri yok.</p>;
  }
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {withLeaders.map((sector) => (
        <div key={sector.symbol} className="rounded-lg border border-border p-3">
          <p className="mb-2 text-xs font-medium text-text-dim">
            {sector.symbol} · {sector.label_tr}
          </p>
          <ul className="flex flex-col gap-1">
            {leaders[sector.symbol].map((leader, i) => (
              <li key={leader.symbol} className="flex items-center justify-between text-sm">
                <span className="text-text">
                  <span className="mr-1.5 text-text-faint">{i + 1}.</span>
                  {leader.symbol}
                </span>
                <span className={`tabular ${leader.perf_1m >= 0 ? "text-pos" : "text-neg"}`}>
                  {fmtPct(leader.perf_1m, 1)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
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
