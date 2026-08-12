import type { SymbolReport } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { fmtMoney, fmtPct } from "@/lib/format";

const RSI_ZONE_LABEL: Record<NonNullable<SymbolReport["rsi_zone"]>, string> = {
  asiri_alim: "Aşırı Alım",
  asiri_satim: "Aşırı Satım",
  notr: "Nötr",
};

const LEVEL_LABEL: Record<NonNullable<SymbolReport["price_vs_sma50"]>, string> = {
  ustunde: "Üstünde",
  altinda: "Altında",
};

const OBV_LABEL: Record<SymbolReport["obv_trend"], string> = {
  yukselis: "Yükseliş",
  dusus: "Düşüş",
  yatay: "Yatay",
};

const CMF_LABEL: Record<SymbolReport["cmf_signal"], string> = {
  accumulation: "Birikim",
  distribution: "Dağıtım",
  notr: "Nötr",
};

function slopeLabel(rising: boolean | null): string {
  if (rising === null) return "—";
  return rising ? "Yükseliyor" : "Düşüyor";
}

function slopeTone(rising: boolean | null): "pos" | "neg" | "neutral" {
  if (rising === null) return "neutral";
  return rising ? "pos" : "neg";
}

function Badge({ label, value, tone = "neutral" }: {
  label: string;
  value: string;
  tone?: "pos" | "neg" | "neutral";
}) {
  const toneClass =
    tone === "pos" ? "text-pos" : tone === "neg" ? "text-neg" : "text-text-dim";
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-0">
      <span className="text-text-faint">{label}</span>
      <span className={`font-medium ${toneClass}`}>{value}</span>
    </div>
  );
}

export function ReportPanel({ report: r }: { report: SymbolReport }) {
  return (
    <Panel
      title={`${r.symbol} — Teknik Durum Raporu`}
      subtitle="Mekanik teknik durum özeti, fiyat/hacim/indikatörlerden üretildi -- bir tahmin veya yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-6">
        <div className="flex items-baseline gap-3">
          <span className="text-2xl font-semibold tabular text-text">
            {fmtMoney(r.price, "USD")}
          </span>
          <span className={`tabular text-sm font-medium ${r.change_1d >= 0 ? "text-pos" : "text-neg"}`}>
            {fmtPct(r.change_1d, 2)}
          </span>
        </div>

        <p className="text-sm leading-relaxed text-text-dim">{r.summary_tr}</p>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <StatTile label="RSI (14)" value={r.rsi !== null ? r.rsi.toFixed(0) : "—"} />
          <StatTile label="ATR (14)" value={r.atr_14 !== null ? r.atr_14.toFixed(2) : "—"} />
          <StatTile label="ADR%" value={r.adr_pct !== null ? `%${r.adr_pct.toFixed(1)}` : "—"} />
          <StatTile
            label="Range Daralması"
            value={r.range_contraction_pct !== null ? `%${r.range_contraction_pct.toFixed(0)}` : "—"}
          />
          <StatTile
            label="Hacim Daralması"
            value={r.volume_contraction_pct !== null ? `%${r.volume_contraction_pct.toFixed(0)}` : "—"}
          />
          <StatTile label="MFI (14)" value={r.mfi !== null ? r.mfi.toFixed(0) : "—"} />
          <StatTile label="CMF (20)" value={r.cmf !== null ? r.cmf.toFixed(2) : "—"} />
          <StatTile
            label="Hacim / 20g Ort."
            value={r.volume_vs_avg_pct !== null ? fmtPct(r.volume_vs_avg_pct, 0) : "—"}
          />
          <StatTile
            label="52h Zirveden"
            value={r.pct_from_52w_high !== null ? fmtPct(r.pct_from_52w_high, 1) : "—"}
          />
          <StatTile
            label="52h Dipten"
            value={r.pct_from_52w_low !== null ? fmtPct(r.pct_from_52w_low, 1) : "—"}
          />
        </div>

        <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
          <div className="flex flex-col">
            <Badge label="EMA21" value={slopeLabel(r.ema21_rising)} tone={slopeTone(r.ema21_rising)} />
            <Badge label="EMA50" value={slopeLabel(r.ema50_rising)} tone={slopeTone(r.ema50_rising)} />
            <Badge
              label="Fiyat vs SMA50"
              value={r.price_vs_sma50 ? LEVEL_LABEL[r.price_vs_sma50] : "—"}
              tone={r.price_vs_sma50 === "ustunde" ? "pos" : r.price_vs_sma50 === "altinda" ? "neg" : "neutral"}
            />
            <Badge
              label="Fiyat vs SMA200"
              value={r.price_vs_sma200 ? LEVEL_LABEL[r.price_vs_sma200] : "—"}
              tone={r.price_vs_sma200 === "ustunde" ? "pos" : r.price_vs_sma200 === "altinda" ? "neg" : "neutral"}
            />
            <Badge
              label="Haftalık Trend"
              value={slopeLabel(r.weekly_trend_aligned)}
              tone={slopeTone(r.weekly_trend_aligned)}
            />
          </div>
          <div className="flex flex-col">
            <Badge
              label="RSI Bölgesi"
              value={r.rsi_zone ? RSI_ZONE_LABEL[r.rsi_zone] : "—"}
              tone={r.rsi_zone === "asiri_alim" ? "neg" : r.rsi_zone === "asiri_satim" ? "pos" : "neutral"}
            />
            <Badge label="OBV" value={OBV_LABEL[r.obv_trend]} tone={slopeTone(r.obv_trend === "yatay" ? null : r.obv_trend === "yukselis")} />
            <Badge
              label="Para Akışı (CMF)"
              value={CMF_LABEL[r.cmf_signal]}
              tone={r.cmf_signal === "accumulation" ? "pos" : r.cmf_signal === "distribution" ? "neg" : "neutral"}
            />
            <Badge
              label="My Trade — Long"
              value={r.matched_long_groups.length > 0 ? `Grup ${r.matched_long_groups.join(", ")}` : "Eşleşme yok"}
              tone={r.matched_long_groups.length > 0 ? "pos" : "neutral"}
            />
            <Badge
              label="My Trade — Short"
              value={r.matched_short_groups.length > 0 ? `Grup ${r.matched_short_groups.join(", ")}` : "Eşleşme yok"}
              tone={r.matched_short_groups.length > 0 ? "neg" : "neutral"}
            />
          </div>
        </div>
      </div>
    </Panel>
  );
}
