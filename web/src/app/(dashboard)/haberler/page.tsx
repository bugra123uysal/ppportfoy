import Link from "next/link";
import { getNews, getPositions } from "@/lib/api";
import type { NewsItem } from "@/lib/api";
import { Panel } from "@/components/panel";
import { timeAgo } from "@/lib/format";

export default async function NewsPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol: selected } = await searchParams;
  const { metrics } = await getPositions();
  const symbols = metrics.map((m) => m.symbol);

  if (symbols.length === 0) {
    return (
      <>
        <h1 className="text-lg font-semibold text-text">Haberler</h1>
        <p className="text-sm text-text-faint">Pozisyon yok.</p>
      </>
    );
  }

  const targets = selected && symbols.includes(selected) ? [selected] : symbols;
  const items = (await Promise.all(targets.map((sym) => getNews(sym, "tr"))))
    .flat()
    .sort((a, b) => (a.published < b.published ? 1 : -1))
    .slice(0, 40);

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Haberler</h1>
        <p className="mt-1 text-sm text-text-faint">
          Holdinglerin için Yahoo Finance + Google News, birleştirilmiş.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterChip href="/haberler" active={!selected} label="Tümü" />
        {symbols.map((sym) => (
          <FilterChip key={sym} href={`/haberler?symbol=${sym}`} active={selected === sym} label={sym} />
        ))}
      </div>

      <Panel title="Akış">
        {items.length === 0 ? (
          <p className="text-sm text-text-faint">Haber bulunamadı.</p>
        ) : (
          <div className="flex flex-col gap-1">
            {items.map((item, i) => (
              <NewsCard key={`${item.link}-${i}`} item={item} />
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}

function FilterChip({ href, active, label }: { href: string; active: boolean; label: string }) {
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

function NewsCard({ item }: { item: NewsItem }) {
  const age = timeAgo(item.published);
  return (
    <a
      href={item.link}
      target="_blank"
      rel="noopener noreferrer"
      className="flex flex-col gap-1 rounded-lg border-b border-border/60 px-2 py-3 transition-colors last:border-0 hover:bg-surface-2"
    >
      <div className="flex items-center gap-2">
        <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium text-text-dim">
          {item.symbol}
        </span>
        <span className="text-sm text-text">{item.title}</span>
      </div>
      <p className="text-xs text-text-faint">
        {item.source}
        {age && ` · ${age}`}
      </p>
    </a>
  );
}
