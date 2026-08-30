"use server";

import { getTrendTradeOverlap, type TrendTradeOverlapPayload } from "@/lib/api";

export interface TrendTradeOverlapState {
  data: TrendTradeOverlapPayload | null;
  error: string | null;
}

export async function runTrendTradeOverlapAction(): Promise<TrendTradeOverlapState> {
  try {
    const data = await getTrendTradeOverlap();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}
