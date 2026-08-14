import { getMarketPulse } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";

// Headline digest for the whole page -- synthesizes breadth, sentiment,
// yield-curve/credit-stress and macro tickers (the same cached reads the
// panels below already fetch independently) into one "is this risk-on or
// risk-off right now, and why" read. Renders nothing when NVIDIA_API_KEY
// isn't configured or the call failed -- the rest of the page never depends
// on this panel.
export async function MarketPulsePanel() {
  const { commentary } = await getMarketPulse();
  if (!commentary) return null;

  return (
    <Panel
      title="Piyasa Nabzı · Nemotron AI"
      subtitle="Aşağıdaki göstergelerin (genişlik, duygu, getiri eğrisi, makro) birlikte ne anlattığını özetler ve genel bir ders çıkarır -- yatırım tavsiyesi değildir."
    >
      <AiCommentary text={commentary} />
    </Panel>
  );
}
