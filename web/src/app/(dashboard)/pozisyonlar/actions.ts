"use server";

import { revalidatePath } from "next/cache";
import { addPosition, ApiMutationError, removePosition } from "@/lib/api";

export interface FormState {
  error: string | null;
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiMutationError) {
    if (err.status === 503) {
      return "Kalıcı depolama yapılandırılmamış (Upstash gerekli).";
    }
    if (
      err.body &&
      typeof err.body === "object" &&
      "error" in err.body &&
      typeof (err.body as { error: unknown }).error === "string"
    ) {
      return (err.body as { error: string }).error;
    }
  }
  return "Bir hata oluştu, tekrar dene.";
}

export async function addPositionAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    await addPosition({
      symbol: String(formData.get("symbol") ?? ""),
      quantity: Number(formData.get("quantity")),
      avg_cost: Number(formData.get("avg_cost")),
      notes: String(formData.get("notes") ?? ""),
    });
  } catch (err) {
    return { error: errorMessage(err) };
  }
  revalidatePath("/pozisyonlar");
  return { error: null };
}

export async function removePositionAction(symbol: string): Promise<FormState> {
  try {
    await removePosition(symbol);
  } catch (err) {
    return { error: errorMessage(err) };
  }
  revalidatePath("/pozisyonlar");
  return { error: null };
}
