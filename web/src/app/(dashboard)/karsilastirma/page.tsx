import Link from "next/link";
import { getCompare } from "@/lib/api";
import { Panel } from "@/components/panel";
import { LineChart } from "@/components/line-chart";
import { fmtPct } from "@/lib/format";

const PERIODS: Record<string, string> = {
  per_1m: "1 Ay",
  per_3m: "3 Ay",
  per_6m: "6 Ay",
  per_ytd: "Yıl Başı",
  per_1y: "1 Yıl",
};
const DEFAULT_PERIOD = "per_3m";
const BASES = ["USD", "TRY"] as const;

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ period?: string; base?: string }>;
}) {
  const params = await searchParams;
  const period = params.period && params.period in PERIODS ? params.period : DEFAULT_PERIOD;
  const base = params.base === "TRY" ? "TRY" : "USD";

  const results = await getCompare(period, base);
  const mine = results.find((r) => r.key === "portfolio");
  const others = results.filter((r) => r.key !== "portfolio");
  const beaten = mine ? others.filter((r) => mine.return_pct > r.return_pct).length : 0;

  const series = results.map((r) => ({
    key: r.key,
    emphasis: r.key === "portfolio",
    points: r.series.dates
      .map((d, i) => ({ x: new Date(d).getTime(), y: r.series.values[i] }))
      .filter((p): p is { x: number; y: number } => p.y !== null),
  }));

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Getiri Karşılaştırma</h1>
        <p className="mt-1 text-sm text-text-faint">
          Bugünkü holdinglerinle &ldquo;buy and hold&rdquo; simülasyonu, endeks/altın/dolar/BTC&apos;ye karşı.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex gap-1.5">
          {BASES.map((b) => (
            <Chip key={b} href={buildHref(period, b)} active={base === b} label={b} />
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(PERIODS).map(([key, label]) => (
            <Chip key={key} href={buildHref(key, base)} active={period === key} label={label} />
          ))}
        </div>
      </div>

      {results.length === 0 ? (
        <p className="text-sm text-text-faint">Yeterli veri yok.</p>
      ) : (
        <>
          {mine && (
            <p className="text-sm text-text">
              Portföyün {others.length} varlıktan <span className="font-semibold text-accent">{beaten}</span> tanesini geride bıraktı ·{" "}
              <span className={mine.return_pct >= 0 ? "text-pos" : "text-neg"}>
                {fmtPct(mine.return_pct, 2)}
              </span>
            </p>
          )}

          <Panel title="Getiri Yarışı">
            <LineChart series={series} />
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
              {results.map((r) => (
                <div key={r.key} className="flex items-center gap-2 text-xs">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${r.key === "portfolio" ? "bg-accent" : "bg-text-faint"}`}
                  />
                  <span className="text-text">{r.key === "portfolio" ? "Portföyüm" : r.label_tr}</span>
                  <span className={`tabular ${r.return_pct >= 0 ? "text-pos" : "text-neg"}`}>
                    {fmtPct(r.return_pct, 1)}
                  </span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Sıralama">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[420px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-text-faint">
                    <th className="py-2 pr-4 font-medium">Sıra</th>
                    <th className="py-2 pr-4 font-medium">Varlık</th>
                    <th className="py-2 pr-4 text-right font-medium">Getiri</th>
                    <th className="py-2 text-right font-medium">Portföye Fark</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    const vs = mine ? r.return_pct - mine.return_pct : 0;
                    return (
                      <tr key={r.key} className="border-b border-border/60 last:border-0">
                        <td className="py-2.5 pr-4 text-text-faint">{i + 1}</td>
                        <td className="py-2.5 pr-4 font-medium text-text">
                          {r.key === "portfolio" ? "Portföyüm" : r.label_tr}
                        </td>
                        <td
                          className={`tabular py-2.5 pr-4 text-right ${r.return_pct >= 0 ? "text-pos" : "text-neg"}`}
                        >
                          {fmtPct(r.return_pct, 2)}
                        </td>
                        <td className={`tabular py-2.5 text-right ${vs >= 0 ? "text-pos" : "text-neg"}`}>
                          {fmtPct(vs, 2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </>
  );
}

function buildHref(period: string, base: string): string {
  return `/karsilastirma?period=${period}&base=${base}`;
}

function Chip({ href, active, label }: { href: string; active: boolean; label: string }) {
  return (
    <Link
      href={href}
      className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
        active
          ? "border-accent bg-accent-soft text-accent"
          : "border-border text-text-dim hover:border-border-strong hover:text-text"
      }`}
    >
      {label}
    </Link>
  );
}
