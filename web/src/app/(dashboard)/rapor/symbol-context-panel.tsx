import type { SymbolContext } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { fmtCompact, fmtPct } from "@/lib/format";

const MOOD_LABEL: Record<NonNullable<SymbolContext["pcr_mood"]>, string> = {
  bearish: "Bearish (koruma ağırlıklı)",
  bullish: "Bullish (call ağırlıklı)",
  neutral: "Nötr",
};

function moodTone(mood: SymbolContext["pcr_mood"]): "pos" | "neg" | "neutral" {
  if (mood === "bearish") return "neg";
  if (mood === "bullish") return "pos";
  return "neutral";
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

export function SymbolContextPanel({ context }: { context: SymbolContext }) {
  if (context.unavailable_reason === "bist") {
    return (
      <Panel title="Opsiyon &amp; Kurumsal Yatırımcı Verisi">
        <p className="text-sm text-text-faint">
          Yahoo/yfinance, BIST (.IS) sembolleri için opsiyon zinciri veya kurumsal sahiplik verisi
          sağlamıyor — bu alan yalnızca ABD hisseleri için dolduruluyor.
        </p>
      </Panel>
    );
  }

  if (context.unavailable_reason === "no_data") {
    return (
      <Panel title="Opsiyon &amp; Kurumsal Yatırımcı Verisi">
        <p className="text-sm text-text-faint">
          Bu sembol için Yahoo&apos;dan şu an opsiyon veya sahiplik verisi dönmedi — geçici bir
          eksiklik olabilir, daha sonra tekrar dene.
        </p>
      </Panel>
    );
  }

  const putCallRatio = context.put_call_ratio;
  const hasOptions = putCallRatio !== null;
  const hasOwnership = context.institutional_pct !== null || context.insider_net_pct_6m !== null;

  return (
    <Panel
      title="Opsiyon &amp; Kurumsal Yatırımcı Verisi"
      subtitle="Yahoo/yfinance üzerinden, ~15 dk gecikmeli opsiyon verisi ve en son bildirilen sahiplik oranları -- sadece ABD hisseleri için."
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatTile
          label="Put/Call Oranı"
          value={putCallRatio !== null ? putCallRatio.toFixed(2) : "—"}
          delta={context.pcr_mood ? MOOD_LABEL[context.pcr_mood] : undefined}
          deltaTone={moodTone(context.pcr_mood)}
        />
        <StatTile
          label="Call Hacmi"
          value={context.call_volume !== null ? fmtCompact(context.call_volume) : "—"}
        />
        <StatTile
          label="Put Hacmi"
          value={context.put_volume !== null ? fmtCompact(context.put_volume) : "—"}
        />
        <StatTile
          label="Vade"
          value={context.option_expiry ? fmtDate(context.option_expiry) : "—"}
        />
        <StatTile
          label="Kurumsal Sahiplik"
          value={context.institutional_pct !== null ? fmtPct(context.institutional_pct, 1) : "—"}
        />
        <StatTile
          label="İçeriden Net Alım (6a)"
          value={
            context.insider_net_pct_6m !== null ? fmtPct(context.insider_net_pct_6m, 1) : "—"
          }
          deltaTone={
            context.insider_net_pct_6m !== null
              ? context.insider_net_pct_6m >= 0
                ? "pos"
                : "neg"
              : "neutral"
          }
        />
      </div>

      {!hasOptions && !hasOwnership && (
        <p className="mt-4 text-xs text-text-faint">
          Bu sembol için opsiyon ve sahiplik verisinin bir kısmı Yahoo&apos;da mevcut değil.
        </p>
      )}
    </Panel>
  );
}
