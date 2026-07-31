import type { Alert } from "@/lib/api";

const TEMPLATES: Record<string, string> = {
  al_below_sma_slow: "{symbol}: Fiyat 200 günlük ortalamanın ALTINDA — uzun vadeli trend kırık.",
  al_below_sma_fast: "{symbol}: Fiyat 50 günlük ortalamanın altında — momentum zayıflıyor.",
  al_rsi_over: "{symbol}: RSI {value} — aşırı alım bölgesi, kâr realizasyonu gelebilir.",
  al_rsi_under: "{symbol}: RSI {value} — aşırı satım bölgesi.",
  al_daily_drop: "{symbol}: Bugün %{value} düştü — haber akışını kontrol et.",
  al_loss: "{symbol}: Maliyetine göre %{value} zararda — stop planını gözden geçir.",
  al_earnings: "{symbol}: Bilanço tarihi yaklaşıyor ({date}) — oynaklık artabilir.",
  al_concentration: "{symbol} portföyün %{value}'ini oluşturuyor — konsantrasyon riski.",
  al_vix: "VIX {value} — piyasa geneli stres yüksek, pozisyon boyutlarına dikkat.",
  al_near_stop: "{symbol}: Fiyat ATR stop seviyesine çok yakın ({value}).",
};

export function alertText(alert: Alert): string {
  const template = TEMPLATES[alert.key] ?? alert.key;
  return template.replace(/\{(\w+)\}/g, (_, key: string) => alert.params[key] ?? "");
}

export const SEVERITY_LABEL: Record<Alert["severity"], string> = {
  crit: "KRİTİK",
  warn: "UYARI",
  info: "BİLGİ",
};
