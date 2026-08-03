import { getOptionsScan } from "@/lib/api";
import type { OptionActivity } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { OptionsTable } from "./options-table";
import { putCallRatio, totalVolume } from "./mood";

export default async function OptionsPage() {
  const activities = await getOptionsScan();

  if (activities.length === 0) {
    return (
      <>
        <h1 className="text-lg font-semibold text-text">Opsiyon Radarı</h1>
        <p className="text-sm text-text-faint">Veri alınamadı.</p>
      </>
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
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Opsiyon Radarı</h1>
        <p className="mt-1 text-sm text-text-faint">
          En likit ABD hisselerinde call/put hacmi, ~15 dk gecikmeli (Yahoo).
        </p>
      </div>

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

      <Panel title="Hacim Sıralaması" subtitle="Put/Call oranı 1.0+ ayı, 0.7- boğa eğilimini gösterir">
        <OptionsTable activities={activities} />
      </Panel>
    </>
  );
}
