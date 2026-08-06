import { Suspense } from "react";
import { PanelSkeleton } from "@/components/skeleton";
import { MacroPanel } from "./macro-panel";
import { PortfolioOverview } from "./portfolio-overview";

export default function OverviewPage() {
  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Genel Bakış</h1>
        <p className="mt-1 text-sm text-text-faint">
          Eğitim amaçlıdır, yatırım tavsiyesi değildir.
        </p>
      </div>

      <Suspense fallback={<PanelSkeleton />}>
        <MacroPanel />
      </Suspense>

      <Suspense fallback={<PanelSkeleton />}>
        <PortfolioOverview />
      </Suspense>
    </>
  );
}
