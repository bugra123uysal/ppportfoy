import { getOptionsScan } from "@/lib/api";
import type { OptionActivity } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";

const PCR_BEARISH = 1.0;
const PCR_BULLISH = 0.7;

function totalVolume(a: OptionActivity): number {
  return a.call_volume + a.put_volume;
}

function putCallRatio(a: OptionActivity): number | null {
  return a.call_volume > 0 ? a.put_volume / a.call_volume : null;
}

function pcrMood(ratio: number | null): "bearish" | "bullish" | "neutral" {
  if (ratio === null) return "neutral";
  if (ratio >= PCR_BEARISH) return "bearish";
  if (ratio <= PCR_BULLISH) return "bullish";
  return "neutral";
}

const MOOD_LABEL: Record<string, string> = {
  bearish: "Ayı",
  bullish: "Boğa",
  neutral: "Nötr",
};

const MOOD_TONE: Record<string, string> = {
  bearish: "text-neg",
  bullish: "text-pos",
  neutral: "text-text-faint",
};

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
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-text-faint">
                <th className="py-2 pr-4 font-medium">Sembol</th>
                <th className="py-2 pr-4 font-medium">Vade</th>
                <th className="py-2 pr-4 text-right font-medium">Call</th>
                <th className="py-2 pr-4 text-right font-medium">Put</th>
                <th className="py-2 pr-4 text-right font-medium">Toplam</th>
                <th className="py-2 pr-4 text-right font-medium">PCR</th>
                <th className="py-2 text-right font-medium">Eğilim</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => {
                const ratio = putCallRatio(a);
                const mood = pcrMood(ratio);
                return (
                  <tr key={a.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{a.symbol}</td>
                    <td className="py-2.5 pr-4 text-text-dim">{a.expiry}</td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {a.call_volume.toLocaleString("tr-TR")}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {a.put_volume.toLocaleString("tr-TR")}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text">
                      {totalVolume(a).toLocaleString("tr-TR")}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {ratio !== null ? ratio.toFixed(2) : "—"}
                    </td>
                    <td className={`py-2.5 text-right text-xs font-medium ${MOOD_TONE[mood]}`}>
                      {MOOD_LABEL[mood]}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
