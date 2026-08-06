import { getPortfolioSummary, getPositions } from "@/lib/api";
import { fmtMoney, fmtPct } from "@/lib/format";
import { StatTile } from "@/components/stat-tile";
import { Panel } from "@/components/panel";
import { AllocationBar } from "@/components/allocation-bar";
import { PnlBars } from "@/components/pnl-bars";

// Live P&L, so both fetches stay `no-store` -- this is the panel most
// likely to be the slowest thing on the page, kept in its own Suspense
// boundary so it doesn't hold up the (cached, fast) macro strip above it.
export async function PortfolioOverview() {
  const [positions, summary] = await Promise.all([getPositions(), getPortfolioSummary()]);
  const { metrics } = positions;
  const { totals } = summary;

  return (
    <>
      <div>
        <p className="text-xs text-text-dim">Toplam Değer</p>
        <p className="tabular mt-1 text-5xl font-semibold text-text">
          {fmtMoney(totals.value_try, "TRY")}
        </p>
        <p className="tabular mt-1 text-sm text-text-dim">
          {fmtMoney(totals.value_usd, "USD")}
        </p>
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

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Portföy Dağılımı" subtitle="Ağırlığa göre, ABD doları bazında">
          <AllocationBar metrics={metrics} />
        </Panel>
        <Panel title="Pozisyon Bazında K/Z" subtitle="Maliyete göre kâr/zarar yüzdesi">
          <PnlBars metrics={metrics} />
        </Panel>
      </div>
    </>
  );
}
