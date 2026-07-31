interface StatTileProps {
  label: string;
  value: string;
  delta?: string;
  deltaTone?: "pos" | "neg" | "neutral";
}

export function StatTile({ label, value, delta, deltaTone = "neutral" }: StatTileProps) {
  return (
    <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-surface px-5 py-4">
      <p className="text-xs text-text-dim">{label}</p>
      <p className="text-2xl font-semibold text-text">{value}</p>
      {delta && (
        <p
          className={`text-xs font-medium tabular ${
            deltaTone === "pos" ? "text-pos" : deltaTone === "neg" ? "text-neg" : "text-text-faint"
          }`}
        >
          {delta}
        </p>
      )}
    </div>
  );
}
