"use server";

import {
  getFundamentals,
  getMoneyFlow,
  getTradeScan,
  getVcpScan,
  type FundamentalScanPayload,
  type MoneyFlowPayload,
  type TradeScanPayload,
  type VcpScanPayload,
} from "@/lib/api";

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

export interface FundamentalScanState {
  data: FundamentalScanPayload | null;
  error: string | null;
}

export async function runFundamentalScanAction(): Promise<FundamentalScanState> {
  try {
    const data = await getFundamentals();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}

export interface VcpScanState {
  data: VcpScanPayload | null;
  error: string | null;
}

export async function runVcpScanAction(): Promise<VcpScanState> {
  try {
    const data = await getVcpScan();
    return { data, error: null };
  } catch {
    return { data: null, error: "Tarama başarısız oldu, tekrar dene." };
  }
}
