import type { OptionActivity } from "@/lib/api";

const PCR_BEARISH = 1.0;
const PCR_BULLISH = 0.7;

export function totalVolume(a: OptionActivity): number {
  return a.call_volume + a.put_volume;
}

export function putCallRatio(a: OptionActivity): number | null {
  return a.call_volume > 0 ? a.put_volume / a.call_volume : null;
}

export type Mood = "bearish" | "bullish" | "neutral";

export function pcrMood(ratio: number | null): Mood {
  if (ratio === null) return "neutral";
  if (ratio >= PCR_BEARISH) return "bearish";
  if (ratio <= PCR_BULLISH) return "bullish";
  return "neutral";
}

export const MOOD_LABEL: Record<Mood, string> = {
  bearish: "Ayı",
  bullish: "Boğa",
  neutral: "Nötr",
};

export const MOOD_TONE: Record<Mood, string> = {
  bearish: "text-neg",
  bullish: "text-pos",
  neutral: "text-text-faint",
};
