import { Suspense } from "react";
import { getPortfolioSummary, getPositions } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { AllocationPie } from "@/components/allocation-pie";
import { PanelSkeleton } from "@/components/skeleton";
import { fmtMoney, fmtPct } from "@/lib/format";
import { AddPositionForm } from "./add-position-form";
import { AnalystSection } from "./analyst-section";
import { PositionsTable } from "./positions-table";

export async function PositionsOverview() {
  const [{ metrics, cash }, { totals }] = await Promise.all([
    getPositions(),
    getPortfolioSummary(),
  ]);

  return (
    <>
      <div>
        <p className="text-xs text-text-dim">Toplam Değer</p>
        <p className="tabular mt-1 text-5xl font-semibold text-text">
          {fmtMoney(totals.value_try, "TRY")}
        </p>
        <p className="tabular mt-1 text-sm text-text-dim">{fmtMoney(totals.value_usd, "USD")}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Yatırım" value={fmtMoney(totals.invested_try, "TRY")} />
        <StatTile label="Nakit" value={fmtMoney(totals.cash_try, "TRY")} />
        <StatTile
          label="Toplam K/Z"
          value={fmtMoney(totals.pnl_usd, "USD")}
          delta={fmtPct(totals.pnl_pct)}
          deltaTone={totals.pnl_pct >= 0 ? "pos" : "neg"}
        />
        <StatTile
          label="Günlük Değişim"
          value={fmtPct(totals.daily_pct)}
          deltaTone={totals.daily_pct >= 0 ? "pos" : "neg"}
        />
      </div>

      <div className={cash.length > 0 ? "grid gap-6 lg:grid-cols-[1.2fr_1fr]" : "flex flex-col gap-6"}>
        <Panel title="Portföy Dağılımı" subtitle="Pozisyon ve nakit, ABD doları bazında ağırlık">
          <AllocationPie
            metrics={metrics}
            cashWeight={totals.cash_weight}
            cashValueUsd={totals.cash_usd}
            totalValueTry={totals.value_try}
            positionCount={metrics.length}
          />
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
      </div>

      <Panel title="Pozisyon Ekle">
        <AddPositionForm />
      </Panel>

      <Panel title="Holdinglerim">
        {metrics.length === 0 ? (
          <p className="text-sm text-text-faint">Pozisyon yok.</p>
        ) : (
          <PositionsTable metrics={metrics} />
        )}
      </Panel>

      <Suspense fallback={<PanelSkeleton />}>
        <AnalystSection metrics={metrics} />
      </Suspense>
    </>
  );
}
