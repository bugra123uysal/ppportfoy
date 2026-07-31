import { createHash } from "node:crypto";

const COOKIE_NAME = "portfoy_session";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

/**
 * Deterministic from SITE_PASSWORD alone, so no separate session secret has
 * to be provisioned: only someone who knows the password can produce the
 * token that unlocks the cookie.
 */
function sessionToken(password: string): string {
  return createHash("sha256").update(`portfoy_session:${password}`).digest("hex");
}

function expectedToken(): string | null {
  const password = process.env.SITE_PASSWORD;
  return password ? sessionToken(password) : null;
}

export function isValidSession(cookieValue: string | undefined): boolean {
  const expected = expectedToken();
  if (!expected || !cookieValue || cookieValue.length !== expected.length) {
    return false;
  }
  // Fixed-length hex digests, so a plain loop is a fine constant-time compare
  // without pulling in Buffer/timingSafeEqual for two short hex strings.
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ cookieValue.charCodeAt(i);
  }
  return diff === 0;
}

export function sessionCookie(password: string) {
  return {
    name: COOKIE_NAME,
    value: sessionToken(password),
    httpOnly: true,
    // The Secure attribute blocks the cookie from ever being set over plain
    // HTTP -- correct in production (Vercel is always HTTPS), but it would
    // silently no-op on `npm run dev`'s http://localhost.
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  };
}

export { COOKIE_NAME };
