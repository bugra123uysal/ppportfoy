"use server";

import { getMoneyFlow, getTradeScan, type MoneyFlowPayload, type TradeScanPayload } from "@/lib/api";

export interface TradeScanState {
  data: TradeScanPayload | null;
  error: string | null;
}

export async function runTradeScanAction(): Promise<TradeScanState> {
  try {
    const data = await getTradeScan();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}

export interface MoneyFlowState {
  data: MoneyFlowPayload | null;
  error: string | null;
}

export async function runMoneyFlowScanAction(): Promise<MoneyFlowState> {
  try {
    const data = await getMoneyFlow();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}
