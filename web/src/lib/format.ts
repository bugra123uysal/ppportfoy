export function fmtMoney(value: number, currency: "TRY" | "USD"): string {
  const symbol = currency === "TRY" ? "₺" : "$";
  return `${symbol}${Math.round(value).toLocaleString("tr-TR")}`;
}

export function fmtPct(value: number, digits = 1): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function timeAgo(isoDate: string): string {
  const published = new Date(isoDate);
  if (published.getUTCFullYear() <= 1970) return "";
  const hours = Math.floor((Date.now() - published.getTime()) / 3_600_000);
  if (hours < 1) return "az önce";
  if (hours < 24) return `${hours} saat önce`;
  return `${Math.floor(hours / 24)} gün önce`;
}

export function fmtCompact(value: number): string {
  return new Intl.NumberFormat("tr-TR", { notation: "compact", maximumFractionDigits: 1 }).format(
    value,
  );
}
