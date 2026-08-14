import type { FibLevel, FibLevels, SymbolReport } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { fmtMoney } from "@/lib/format";

const DIRECTION_LABEL: Record<FibLevels["direction"], string> = {
  yukselis: "Yükseliş — tepeden dip yönüne geri çekilme",
  dusus: "Düşüş — dipten tepe yönüne geri çekilme",
};

const KIND_LABEL: Record<FibLevel["kind"], string> = {
  retracement: "Geri Çekilme",
  extension: "Uzantı",
};

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

function LevelRow({
  level,
  currency,
  isNearest,
}: {
  level: FibLevel;
  currency: SymbolReport["currency"];
  isNearest: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm transition-colors ${
        isNearest
          ? "border-accent/60 bg-accent/10"
          : "border-border/60 bg-transparent"
      }`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
            level.kind === "extension" ? "text-text-faint" : "text-text-dim"
          }`}
        >
          {KIND_LABEL[level.kind]}
        </span>
        <span className="tabular font-medium text-text">{level.ratio}</span>
      </div>
      <div className="flex items-center gap-2">
        {isNearest && (
          <span className="rounded-full bg-accent px-2 py-0.5 text-[10px] font-semibold text-black">
            Fiyat Burada
          </span>
        )}
        <span className="tabular font-medium text-text">{fmtMoney(level.price, currency)}</span>
      </div>
    </div>
  );
}

export function FibonacciPanel({
  fib,
  currency,
}: {
  fib: FibLevels;
  currency: SymbolReport["currency"];
}) {
  return (
    <Panel
      title="Fibonacci Seviyeleri"
      subtitle={`Son ${fib.lookback_days} günlük salınım (${DIRECTION_LABEL[fib.direction]}) baz alınarak hesaplandı.`}
    >
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Salınım Tepesi" value={fmtMoney(fib.swing_high, currency)} delta={fmtDate(fib.swing_high_date)} />
          <StatTile label="Salınım Dibi" value={fmtMoney(fib.swing_low, currency)} delta={fmtDate(fib.swing_low_date)} />
          <StatTile label="En Yakın Seviye" value={`${fib.nearest_ratio}`} delta={fmtMoney(fib.nearest_price, currency)} />
          <StatTile
            label="Bölge"
            value={fib.zone_label}
            delta={`${fib.pct_to_nearest >= 0 ? "+" : ""}${fib.pct_to_nearest.toFixed(1)}%`}
            deltaTone={fib.pct_to_nearest >= 0 ? "pos" : "neg"}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          {[...fib.levels]
            .sort((a, b) => b.price - a.price)
            .map((level) => (
              <LevelRow
                key={`${level.kind}-${level.ratio}`}
                level={level}
                currency={currency}
                isNearest={fib.at_level && level.ratio === fib.nearest_ratio}
              />
            ))}
        </div>
      </div>
    </Panel>
  );
}
