import { getPortfolioSummary } from "@/lib/api";
import { Panel } from "@/components/panel";
import { AlertList } from "@/components/alert-list";
import { StatTile } from "@/components/stat-tile";
import { PositionHealthPanel } from "./position-health-panel";

export default async function RiskPage() {
  const { alerts, position_health } = await getPortfolioSummary();
  const crit = alerts.filter((a) => a.severity === "crit").length;
  const warn = alerts.filter((a) => a.severity === "warn").length;
  const info = alerts.filter((a) => a.severity === "info").length;

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Risk & Uyarılar</h1>
        <p className="mt-1 text-sm text-text-faint">
          Pozisyonlarına göre otomatik üretilen uyarılar, en kritikten başlayarak.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatTile label="Kritik" value={String(crit)} deltaTone={crit > 0 ? "neg" : "neutral"} />
        <StatTile label="Uyarı" value={String(warn)} />
        <StatTile label="Bilgi" value={String(info)} />
      </div>

      <Panel title="Aktif Uyarılar">
        <AlertList alerts={alerts} />
      </Panel>

      <PositionHealthPanel health={position_health} />
    </>
  );
}
