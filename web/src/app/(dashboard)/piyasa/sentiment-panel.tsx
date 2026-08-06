import { getSentiment } from "@/lib/api";
import { Panel } from "@/components/panel";
import { SentimentMeter } from "@/components/sentiment-meter";
import { SENTIMENT_COMPONENT_TR } from "@/lib/sentiment";

export async function SentimentPanel() {
  const sentiment = await getSentiment();

  return (
    <Panel title="Duygu & Volatilite" subtitle="Korku mu, iştah mı?">
      {sentiment === null ? (
        <p className="text-sm text-text-faint">Veri alınamadı.</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <SentimentMeter composite={sentiment.composite} />
          <div className="flex flex-col justify-center gap-2">
            {Object.entries(sentiment.components).map(([name, value]) => (
              <div key={name} className="flex items-center justify-between text-sm">
                <span className="text-text-dim">{SENTIMENT_COMPONENT_TR[name] ?? name}</span>
                <span className="tabular font-medium text-text">{value.toFixed(0)} / 100</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}
