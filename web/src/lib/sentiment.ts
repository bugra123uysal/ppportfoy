export type SentimentLabel = "extreme_fear" | "fear" | "neutral" | "greed" | "extreme_greed";

export function sentimentLabel(composite: number): SentimentLabel {
  if (composite < 25) return "extreme_fear";
  if (composite < 45) return "fear";
  if (composite <= 55) return "neutral";
  if (composite <= 75) return "greed";
  return "extreme_greed";
}

export const SENTIMENT_TR: Record<SentimentLabel, string> = {
  extreme_fear: "AŞIRI KORKU",
  fear: "KORKU",
  neutral: "NÖTR",
  greed: "İŞTAH",
  extreme_greed: "AŞIRI İŞTAH",
};

export const SENTIMENT_COMPONENT_TR: Record<string, string> = {
  vix: "VIX (korku endeksi)",
  momentum: "S&P Momentum",
  breadth: "Breadth (katılım)",
  put_call: "SPY Put/Call",
};
