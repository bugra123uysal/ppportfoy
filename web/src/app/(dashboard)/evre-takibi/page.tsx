import { getStageAnalysis } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { StageTable } from "./stage-table";

export default async function StageTrackingPage() {
  const { stages, commentary } = await getStageAnalysis();
  const alerts = stages.filter((s) => s.technical_alert);
  const fresh = alerts.filter((s) => s.stage_changed);
  const advancing = stages.filter((s) => s.stage === 2);

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Evre Takibi</h1>
        <p className="mt-1 text-sm text-text-faint">
          Weinstein&apos;ın 4 evre yöntemi — her pozisyonun 30 haftalık ortalamaya göre hangi evrede
          olduğu ve trendi.
        </p>
      </div>

      {stages.length === 0 ? (
        <Panel title="Evreler">
          <p className="text-sm text-text-faint">
            Pozisyon yok, ya da hiçbir pozisyon için 30 haftalık okuma yapacak kadar geçmiş veri
            henüz mevcut değil.
          </p>
        </Panel>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Toplam Pozisyon" value={String(stages.length)} />
            <StatTile
              label="Teknik Bozukluk"
              value={String(alerts.length)}
              deltaTone={alerts.length > 0 ? "neg" : "neutral"}
            />
            <StatTile
              label="Yeni Evre Geçişi"
              value={String(fresh.length)}
              deltaTone={fresh.length > 0 ? "neg" : "neutral"}
            />
            <StatTile
              label="Evre 2 (Yükseliş)"
              value={String(advancing.length)}
              deltaTone={advancing.length > 0 ? "pos" : "neutral"}
            />
          </div>

          {alerts.length > 0 && (
            <div className="rounded-xl border border-neg/30 bg-neg-soft p-4">
              <p className="text-sm font-medium text-neg">
                ⚠ {alerts.length} pozisyonda teknik bozukluk (Evre 3/4):{" "}
                {alerts.map((s) => s.symbol).join(", ")}
              </p>
            </div>
          )}

          <AiCommentary text={commentary} />

          <Panel
            title="Pozisyon Evreleri"
            subtitle="30 haftalık hareketli ortalama + eğimine göre sınıflandırılır. Evre 3 (tepe) ve Evre 4 (düşüş) teknik bozukluk sayılır."
          >
            <StageTable stages={stages} />
          </Panel>
        </>
      )}
    </>
  );
}
