import { sentimentLabel, SENTIMENT_TR } from "@/lib/sentiment";

export function SentimentMeter({ composite }: { composite: number }) {
  const label = sentimentLabel(composite);
  const clamped = Math.max(0, Math.min(100, composite));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline gap-3">
        <span className="tabular text-4xl font-semibold text-text">{clamped.toFixed(0)}</span>
        <span className="text-xs font-semibold tracking-wide text-text-dim">{SENTIMENT_TR[label]}</span>
      </div>
      <div className="relative h-2.5 w-full rounded-full bg-gradient-to-r from-neg via-text-faint to-pos">
        <div
          className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-text shadow-[0_0_0_2px_var(--surface)]"
          style={{ left: `${clamped}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-text-faint">
        <span>Aşırı Korku</span>
        <span>Nötr</span>
        <span>Aşırı İştah</span>
      </div>
    </div>
  );
}
