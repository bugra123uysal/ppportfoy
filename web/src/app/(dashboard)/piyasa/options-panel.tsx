import { getOptionsScan } from "@/lib/api";
import type { OptionActivity } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { OptionsTable } from "./options-table";
import { putCallRatio, totalVolume } from "./mood";

export async function OptionsPanel() {
  const activities = await getOptionsScan();

  if (activities.length === 0) {
    return (
      <Panel title="Opsiyon Radarı" subtitle="En likit ABD hisselerinde call/put hacmi">
        <p className="text-sm text-text-faint">Veri alınamadı.</p>
      </Panel>
    );
  }

  const busiest = activities[0];
  const withPcr = activities
    .map((a) => ({ a, ratio: putCallRatio(a) }))
    .filter((x): x is { a: OptionActivity; ratio: number } => x.ratio !== null);
  const mostBearish = withPcr.length
    ? withPcr.reduce((max, x) => (x.ratio > max.ratio ? x : max))
    : null;
  const mostBullish = withPcr.length
    ? withPcr.reduce((min, x) => (x.ratio < min.ratio ? x : min))
    : null;

  return (
    <Panel
      title="Opsiyon Radarı"
      subtitle="En likit ABD hisselerinde call/put hacmi, ~15 dk gecikmeli (Yahoo)"
    >
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatTile
            label="En Yoğun"
            value={`${busiest.symbol} · ${totalVolume(busiest).toLocaleString("tr-TR")}`}
          />
          {mostBearish && (
            <StatTile
              label="En Ayı (PCR)"
              value={`${mostBearish.a.symbol} · ${mostBearish.ratio.toFixed(2)}`}
            />
          )}
          {mostBullish && (
            <StatTile
              label="En Boğa (PCR)"
              value={`${mostBullish.a.symbol} · ${mostBullish.ratio.toFixed(2)}`}
            />
          )}
        </div>
        <p className="text-xs text-text-faint">
          Put/Call oranı 1.0+ ayı, 0.7- boğa eğilimini gösterir.
        </p>
        <OptionsTable activities={activities} />
      </div>
    </Panel>
  );
}
