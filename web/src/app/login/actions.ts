"use server";

import { createHash, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { sessionCookie } from "@/lib/auth";
import { safeRedirectTarget } from "@/lib/safe-redirect";

/** Fixed-length digest compare so a plain `!==` on the raw password can't
 * become a byte-by-byte timing side channel against the shared secret. */
function passwordMatches(supplied: string, expected: string): boolean {
  const suppliedHash = createHash("sha256").update(supplied).digest();
  const expectedHash = createHash("sha256").update(expected).digest();
  return timingSafeEqual(suppliedHash, expectedHash);
}

export async function login(_prevState: { error: boolean }, formData: FormData) {
  const password = String(formData.get("password") ?? "");
  const expected = process.env.SITE_PASSWORD ?? "";
  const fromField = formData.get("from");
  const target = safeRedirectTarget(typeof fromField === "string" ? fromField : null);

  if (!expected || !passwordMatches(password, expected)) {
    return { error: true };
  }

  const cookieStore = await cookies();
  cookieStore.set(sessionCookie(password));
  redirect(target);
}
