import { getPositions } from "@/lib/api";
import { Panel } from "@/components/panel";
import { fmtMoney, fmtPct } from "@/lib/format";

export default async function PositionsPage() {
  const { metrics, cash } = await getPositions();

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Pozisyonlar</h1>
        <p className="mt-1 text-sm text-text-faint">
          Salt okunur görünüm — ekleme/silme için Streamlit uygulamasını kullan.
        </p>
      </div>

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
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-text-faint">
                  <th className="py-2 pr-4 font-medium">Sembol</th>
                  <th className="py-2 pr-4 text-right font-medium">Adet</th>
                  <th className="py-2 pr-4 text-right font-medium">Ort. Maliyet</th>
                  <th className="py-2 pr-4 text-right font-medium">Fiyat</th>
                  <th className="py-2 pr-4 text-right font-medium">Günlük %</th>
                  <th className="py-2 pr-4 text-right font-medium">Değer</th>
                  <th className="py-2 pr-4 text-right font-medium">K/Z</th>
                  <th className="py-2 pr-4 text-right font-medium">K/Z %</th>
                  <th className="py-2 text-right font-medium">Ağırlık</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => (
                  <tr key={m.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{m.symbol}</td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {m.quantity.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {m.avg_cost.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text">
                      {m.price.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${m.change_pct >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtPct(m.change_pct)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text">
                      {fmtMoney(m.value, m.currency)}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${m.pnl >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtMoney(m.pnl, m.currency)}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${m.pnl_pct >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtPct(m.pnl_pct)}
                    </td>
                    <td className="tabular py-2.5 text-right text-text-dim">
                      %{(m.weight * 100).toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  );
}
