export interface NavItem {
  href: string;
  label: string;
  glyph: string;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Genel Bakış", glyph: "◉" },
  { href: "/piyasa", label: "Piyasa Pusulası", glyph: "◈" },
  { href: "/pozisyonlar", label: "Pozisyonlar", glyph: "▤" },
  { href: "/risk", label: "Risk & Uyarılar", glyph: "▲" },
  { href: "/karsilastirma", label: "Getiri Karşılaştırma", glyph: "∿" },
  { href: "/my-trade", label: "My Trade", glyph: "⚡" },
  { href: "/trend", label: "Trend Bulucu", glyph: "↗" },
  { href: "/tradingview-tarama", label: "TradingView Tarama", glyph: "◎" },
  { href: "/rapor", label: "Hisse Raporu", glyph: "▣" },
  { href: "/haberler", label: "Haberler", glyph: "▦" },
];
