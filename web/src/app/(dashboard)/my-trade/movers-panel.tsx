import { getMovers } from "@/lib/api";
import type { Mover, NewsItem } from "@/lib/api";
import { Panel } from "@/components/panel";
import { fmtMoney, fmtPct, fmtCompact, timeAgo } from "@/lib/format";

const GROUP_COLOR: Record<number, string> = {
  1: "var(--pos)",
  2: "#3987e5",
  3: "var(--accent)",
  4: "#c084fc",
};

const SENTIMENT_CLASS: Record<NewsItem["sentiment"], string> = {
  positive: "text-pos",
  negative: "text-neg",
  neutral: "text-text-faint",
};

// generated_at can be older than an hour if the scheduled scan hasn't fired
// yet (first deploy, or the external scheduler is misconfigured) -- surface
// that plainly instead of a silently stale-looking table.
function freshnessLabel(generatedAt: string): string {
  const age = timeAgo(generatedAt);
  return age ? `Son tarama: ${age}` : "Son tarama: az önce";
}

export async function MoversPanel() {
  const scan = await getMovers();

  return (
    <Panel
      title="Günün Hareketlileri"
      subtitle={`ABD piyasası — arka planda periyodik taranır (~20 dk), bilgi amaçlıdır, yatırım tavsiyesi değildir. ${freshnessLabel(scan.generated_at)}.`}
    >
      <div className="flex flex-col gap-6">
        <MoversTable
          title="En Çok Yükselenler"
          description="Yahoo'nun günlük sıralaması — zaten hareket etmiş isimler, geriye dönük bir liste."
          movers={scan.gainers}
          emptyText="Şu an veri yok."
        />
        <MoversTable
          title="Hacim Öncüllüğü — Olası Erken Adaylar"
          description="Fiyat henüz büyük hareket etmemişken hacmi 3 aylık ortalamasının kat kat üstüne çıkmış isimler — hacim genelde fiyattan önce gelir."
          movers={scan.volume_spikes}
          emptyText="Şu an eşleşen isim yok."
        />
      </div>
    </Panel>
  );
}

function MoversTable({
  title,
  description,
  movers,
  emptyText,
}: {
  title: string;
  description: string;
  movers: Mover[];
  emptyText: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-1">
        <h3 className="text-xs font-medium text-text-dim">{title}</h3>
        <p className="text-xs text-text-faint">{description}</p>
      </div>
      {movers.length === 0 ? (
        <p className="text-xs text-text-faint">{emptyText}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-text-faint">
                <th className="py-2 pr-4 font-medium">Sembol</th>
                <th className="py-2 pr-4 text-right font-medium">Fiyat</th>
                <th className="py-2 pr-4 text-right font-medium">Değişim</th>
                <th className="py-2 pr-4 text-right font-medium" title="Hacim / 3 aylık ortalama hacim">
                  Hacim Oranı
                </th>
                <th className="py-2 pr-4 font-medium" title="trade_scan Group 1-4 çapraz kontrolü">
                  Sinyal
                </th>
                <th className="py-2 font-medium">Neden?</th>
              </tr>
            </thead>
            <tbody>
              {movers.map((m) => (
                <tr key={m.symbol} className="border-b border-border/60 last:border-0">
                  <td className="py-2.5 pr-4">
                    <div className="font-medium text-text">{m.symbol}</div>
                    <div className="text-xs text-text-faint">{m.name}</div>
                  </td>
                  <td className="tabular py-2.5 pr-4 text-right text-text">
                    {fmtMoney(m.price, "USD")}
                  </td>
                  <td
                    className={`tabular py-2.5 pr-4 text-right ${m.change_pct >= 0 ? "text-pos" : "text-neg"}`}
                  >
                    {fmtPct(m.change_pct, 1)}
                  </td>
                  <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                    {m.relative_volume !== null ? `${m.relative_volume.toFixed(1)}x` : "—"}
                    {m.volume !== null && (
                      <div className="text-xs text-text-faint">{fmtCompact(m.volume)}</div>
                    )}
                  </td>
                  <td className="py-2.5 pr-4">
                    <SignalBadges signals={m.signals} />
                  </td>
                  <td className="py-2.5">
                    <NewsCell news={m.news} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SignalBadges({ signals }: { signals: Mover["signals"] }) {
  if (signals.length === 0) {
    return <span className="text-xs text-text-faint">—</span>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {signals.map((s) => (
        <span
          key={`${s.direction}-${s.groups.join(",")}`}
          className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${
            s.direction === "long" ? "bg-pos-soft text-pos" : "bg-neg-soft text-neg"
          }`}
          title={`trade_scan: ${s.direction === "long" ? "Long" : "Short"} — Grup ${s.groups.join(", ")}`}
        >
          {s.groups.map((g) => (
            <span
              key={g}
              className="h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: GROUP_COLOR[g] }}
              aria-hidden
            />
          ))}
          {s.direction === "long" ? "Long" : "Short"}
        </span>
      ))}
    </div>
  );
}

function NewsCell({ news }: { news: NewsItem[] }) {
  if (news.length === 0) {
    return <span className="text-xs text-text-faint">—</span>;
  }
  const latest = news[0];
  const age = timeAgo(latest.published);
  return (
    <a
      href={latest.link}
      target="_blank"
      rel="noopener noreferrer"
      className="block max-w-[280px] text-xs text-text-dim transition-colors hover:text-accent"
    >
      <span className={SENTIMENT_CLASS[latest.sentiment]}>{latest.title}</span>
      <span className="block text-text-faint">
        {latest.source}
        {age && ` · ${age}`}
      </span>
    </a>
  );
}
