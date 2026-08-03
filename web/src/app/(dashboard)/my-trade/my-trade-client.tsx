"use client";

import { useState } from "react";
import type { TradeSignal } from "@/lib/api";
import { TradeScanPanel } from "./trade-scan-panel";
import { PositionSizeCalculator } from "./position-size-calculator";

export function MyTradeClient() {
  const [selected, setSelected] = useState<TradeSignal | null>(null);

  return (
    <>
      <TradeScanPanel onUseSignal={setSelected} />
      <PositionSizeCalculator prefill={selected} />
    </>
  );
}
