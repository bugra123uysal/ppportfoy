import { Suspense } from "react";
import { PanelSkeleton } from "@/components/skeleton";
import { PositionsOverview } from "./positions-overview";

export default function PositionsPage() {
  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Pozisyonlar</h1>
        <p className="mt-1 text-sm text-text-faint">
          Holdinglerini buradan ekleyip çıkarabilirsin.
        </p>
      </div>

      <Suspense fallback={<PanelSkeleton />}>
        <PositionsOverview />
      </Suspense>
    </>
  );
}
