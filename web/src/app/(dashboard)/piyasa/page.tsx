import { Suspense } from "react";
import { PanelSkeleton } from "@/components/skeleton";
import { BreadthPanel } from "./breadth-panel";
import { YieldCurvePanel } from "./yield-curve-panel";
import { SentimentPanel } from "./sentiment-panel";
import { RotationPanel } from "./rotation-panel";
import { OptionsPanel } from "./options-panel";
import { CalendarPanel } from "./calendar-panel";
import { MarketPulsePanel } from "./market-pulse-panel";

// Each panel below fetches and awaits its own data independently inside its
// own Suspense boundary, instead of one page-level Promise.all -- a panel
// backed by a warm cache (calendar, yield curve, options) renders the moment
// it resolves rather than waiting on the slowest one (breadth/rotation on a
// cold cache) to unblock the whole page.
export default async function MarketCompassPage({
  searchParams,
}: {
  searchParams: Promise<{ mine?: string }>;
}) {
  const { mine } = await searchParams;
  const includeMine = mine === "1";

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Piyasa Pusulası</h1>
        <p className="mt-1 text-sm text-text-faint">
          Piyasayı okumanın tüm katmanları — içeri göstergeler, makro, duygu, sektör rotasyonu,
          opsiyon konumlanması ve takvim, tek sayfada.
        </p>
      </div>

      <Suspense fallback={<PanelSkeleton />}>
        <MarketPulsePanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <BreadthPanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <YieldCurvePanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <SentimentPanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <RotationPanel includeMine={includeMine} />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <OptionsPanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <CalendarPanel />
      </Suspense>
    </>
  );
}
