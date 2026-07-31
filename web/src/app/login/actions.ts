"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { sessionCookie } from "@/lib/auth";

/** Only ever redirect somewhere on this same site -- `from` is an
 * attacker-controllable query param on a page the proxy doesn't protect. */
function safeRedirectTarget(raw: FormDataEntryValue | null): string {
  const value = typeof raw === "string" ? raw : "";
  if (value.startsWith("/") && !value.startsWith("//")) {
    return value;
  }
  return "/";
}

export async function login(_prevState: { error: boolean }, formData: FormData) {
  const password = String(formData.get("password") ?? "");
  const expected = process.env.SITE_PASSWORD ?? "";
  const target = safeRedirectTarget(formData.get("from"));

  if (!expected || password !== expected) {
    return { error: true };
  }

  const cookieStore = await cookies();
  cookieStore.set(sessionCookie(password));
  redirect(target);
}
