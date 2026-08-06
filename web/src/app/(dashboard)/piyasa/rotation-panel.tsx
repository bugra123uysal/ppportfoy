import Link from "next/link";
import { getRotation } from "@/lib/api";
import type { SectorLeader, SectorRotation } from "@/lib/api";
import { Panel } from "@/components/panel";
import { RrgChart } from "@/components/rrg-chart";
import { fmtPct } from "@/lib/format";
import { PerformanceTable } from "./performance-table";

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

export async function RotationPanel({ includeMine }: { includeMine: boolean }) {
  const { sectors: points, leaders } = await getRotation(includeMine);

  // Rotation candidates are always sectors, never the user's own holdings --
  // "rotate into" only makes sense between sectors, even when "Holdinglerimi
  // de göster" overlays individual stocks on the map.
  const sectorSymbols = new Set(Object.keys(leaders));
  const sectorPoints = points.filter((p) => sectorSymbols.has(p.symbol));
  // The RRG scatter specifically stays sector-ETFs-only (plus the user's own
  // holdings when they've asked to see them) -- `points` also carries every
  // individual sector-leader stock (77+ of them, fetched to build the leader
  // accordion + performance table below), which would turn the quadrant into
  // an unreadable dot cloud if plotted directly.
  const chartPoints = points.filter(
    (p) => sectorSymbols.has(p.symbol) || p.label_tr === "Portföyüm",
  );
  // Kadran değişimleri de sadece sektör/ETF bazında gösterilir -- bireysel
  // hisselerin kadran geçişleri listeyi anlamsız derecede kalabalıklaştırır.
  const movers = sectorPoints.filter((p) => p.quadrant !== p.prev_quadrant);
  const candidates = points
    .filter((p) => sectorSymbols.has(p.symbol) && ROTATE_IN_QUADRANTS.has(p.quadrant))
    .sort((a, b) => currentY(b) - currentY(a));
  const topPick = candidates[0];
  const runnerUps = candidates.slice(1, 3);

  return (
    <>
      <Panel
        title="Sektör Rotasyonu"
        subtitle="Relative Rotation Graph (RRG) — sektörler SPY'a göre, kendi aralarında skorlanır"
      >
        <Link
          href={includeMine ? "/piyasa" : "/piyasa?mine=1"}
          className={`mb-4 inline-flex w-fit rounded-full border px-3 py-1.5 text-xs transition-colors ${
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
          <div className="flex flex-col gap-4">
            {topPick ? (
              <div className="flex flex-col gap-2">
                <p className="text-sm text-text">
                  Şu an en güçlü konumda:{" "}
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

            <RrgChart points={chartPoints} />
          </div>
        )}
      </Panel>

      {points.length > 0 && movers.length > 0 && (
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

      {points.length > 0 && (
        <>
          <Panel title="Sektör Başına En İyi 5 Hisse" subtitle="Son 1 ay getirisine göre sıralı">
            <SectorLeaders sectors={points} leaders={leaders} />
          </Panel>

          <Panel title="Sektör Performans Sıralaması">
            <PerformanceTable points={points} />
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
    <div className="flex flex-col divide-y divide-border/60">
      {withLeaders.map((sector) => (
        <details key={sector.symbol} className="group py-2.5 first:pt-0 last:pb-0">
          <summary className="flex cursor-pointer list-none items-center justify-between text-sm">
            <span className="font-medium text-text">
              {sector.symbol} <span className="text-text-faint">· {sector.label_tr}</span>
            </span>
            <span className="text-text-faint transition-transform group-open:rotate-90">›</span>
          </summary>
          <ul className="mt-2 flex flex-col gap-1 pl-1">
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
        </details>
      ))}
    </div>
  );
}
