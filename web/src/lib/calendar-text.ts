import type { MarketEvent } from "@/lib/api";

const KIND_LABEL: Record<MarketEvent["kind"], string> = {
  fomc: "🏛️ Fed Faiz Kararı (FOMC)",
  nfp: "💼 ABD İstihdam Raporu (NFP)",
  earnings: "📊 {symbol} Bilançosu",
};

export function eventLabel(event: MarketEvent): string {
  return KIND_LABEL[event.kind].replace("{symbol}", event.symbol);
}

export function daysLeftText(event: MarketEvent, today: Date): string {
  const when = new Date(event.when);
  const days = Math.round((when.getTime() - today.getTime()) / 86_400_000);
  if (days <= 0) return "BUGÜN";
  return `${days} gün kaldı`;
}
