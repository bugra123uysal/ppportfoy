"use server";

import { getTrendScan, type TrendScanPayload } from "@/lib/api";

export interface TrendScanState {
  data: TrendScanPayload | null;
  error: string | null;
}

export async function runTrendScanAction(): Promise<TrendScanState> {
  try {
    const data = await getTrendScan();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}
