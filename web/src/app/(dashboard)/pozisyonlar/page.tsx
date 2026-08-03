import { getPositions } from "@/lib/api";
import { Panel } from "@/components/panel";
import { fmtMoney } from "@/lib/format";
import { AddPositionForm } from "./add-position-form";
import { PositionsTable } from "./positions-table";

export default async function PositionsPage() {
  const { metrics, cash } = await getPositions();

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Pozisyonlar</h1>
        <p className="mt-1 text-sm text-text-faint">
          Holdinglerini buradan ekleyip çıkarabilirsin.
        </p>
      </div>

      <Panel title="Pozisyon Ekle">
        <AddPositionForm />
      </Panel>

      {cash.length > 0 && (
        <Panel title="Nakit">
          <div className="flex gap-6">
            {cash.map((c) => (
              <div key={c.currency}>
                <p className="text-xs text-text-faint">{c.currency}</p>
                <p className="tabular text-lg font-semibold text-text">
                  {fmtMoney(c.amount, c.currency)}
                </p>
              </div>
            ))}
          </div>
        </Panel>
      )}

      <Panel title="Holdinglerim">
        {metrics.length === 0 ? (
          <p className="text-sm text-text-faint">Pozisyon yok.</p>
        ) : (
          <PositionsTable metrics={metrics} />
        )}
      </Panel>
    </>
  );
}
