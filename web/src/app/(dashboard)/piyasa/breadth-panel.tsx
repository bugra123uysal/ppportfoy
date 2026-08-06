import { getBreadth } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";

const BREADTH_HEALTHY = 60;
const BREADTH_WEAK = 40;

function breadthHealth(pctAbove200: number): { emoji: string; text: string } {
  if (pctAbove200 >= BREADTH_HEALTHY) {
    return { emoji: "🟢", text: "Katılım geniş — yükselişin tabanı sağlam." };
  }
  if (pctAbove200 <= BREADTH_WEAK) {
    return { emoji: "🔴", text: "Katılım dar — endeksi birkaç hisse taşıyor, dikkat." };
  }
  return { emoji: "🟡", text: "Katılım karışık — seçici ol." };
}

export async function BreadthPanel() {
  const breadth = await getBreadth();

  return (
    <Panel title="Piyasa İçi Göstergeler" subtitle="Yükseliş sağlıklı mı?">
      {breadth === null ? (
        <p className="text-sm text-text-faint">Veri alınamadı.</p>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            <StatTile label="SMA50 Üstü" value={`%${breadth.pct_above_50.toFixed(0)}`} />
            <StatTile label="SMA200 Üstü" value={`%${breadth.pct_above_200.toFixed(0)}`} />
            <StatTile
              label="Yükselen / Düşen"
              value={`${breadth.advancers} / ${breadth.decliners}`}
            />
            <StatTile
              label="20g Zirve / Dip"
              value={`${breadth.new_high_20d} / ${breadth.new_low_20d}`}
            />
            <StatTile
              label="TRIN (Arms Index)"
              value={breadth.trin != null ? breadth.trin.toFixed(2) : "—"}
            />
            <StatTile
              label="McClellan Osilatörü"
              value={breadth.mcclellan != null ? breadth.mcclellan.toFixed(0) : "—"}
            />
          </div>
          <p className="text-sm text-text-dim">
            {breadthHealth(breadth.pct_above_200).emoji}{" "}
            {breadthHealth(breadth.pct_above_200).text}
            {breadth.trin != null &&
              (breadth.trin < 1
                ? " Hacim alıcı tarafta yoğunlaşıyor (TRIN < 1)."
                : " Hacim satıcı tarafta yoğunlaşıyor (TRIN > 1).")}
          </p>
        </div>
      )}
    </Panel>
  );
}
