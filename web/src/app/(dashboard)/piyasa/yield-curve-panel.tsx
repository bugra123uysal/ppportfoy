import { getYieldCurve } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { fmtPct } from "@/lib/format";

export async function YieldCurvePanel() {
  const yieldCurve = await getYieldCurve();

  return (
    <Panel title="Getiri Eğrisi & Kredi" subtitle="Resesyon ve kredi riski için erken uyarı sinyalleri">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile
            label="10 Yıllık Tahvil"
            value={yieldCurve.yield_10y !== null ? `%${yieldCurve.yield_10y.toFixed(2)}` : "—"}
          />
          <StatTile
            label="3 Aylık Bono"
            value={yieldCurve.yield_3m !== null ? `%${yieldCurve.yield_3m.toFixed(2)}` : "—"}
          />
          <StatTile
            label="Spread (10Y − 3A)"
            value={
              yieldCurve.spread_10y_3m !== null
                ? `${yieldCurve.spread_10y_3m >= 0 ? "+" : ""}${yieldCurve.spread_10y_3m.toFixed(2)}`
                : "—"
            }
          />
          <StatTile
            label="Kredi Spreadi (HYG/LQD, 1A)"
            value={
              yieldCurve.credit_spread_proxy_change !== null
                ? fmtPct(yieldCurve.credit_spread_proxy_change)
                : "—"
            }
          />
        </div>
        <p className="text-sm text-text-dim">
          {yieldCurve.inverted
            ? "🔴 Getiri eğrisi ters döndü — piyasa resesyon fiyatlıyor, tarihsel olarak güçlü bir öncü sinyal."
            : "🟢 Getiri eğrisi normal — kısa vadeli faiz uzun vadelinin altında."}
          {yieldCurve.credit_stress &&
            " Kredi spreadleri de genişliyor — risk iştahı azalıyor, dikkatli ol."}
        </p>
      </div>
    </Panel>
  );
}
