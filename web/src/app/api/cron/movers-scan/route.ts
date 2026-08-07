import { createHash, timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Public trigger for the movers scan (see portfoy/movers.py + api/index.py's
 * POST /api/movers/scan). Excluded from proxy.ts's password gate -- it's
 * meant to be hit by an external scheduler (GitHub Actions, since Vercel's
 * Hobby plan caps native Cron Jobs at 2/day, far too coarse for an
 * intraday scan) that has no session cookie. CRON_SECRET is this route's
 * own auth instead, checked with the same timing-safe pattern as the site's
 * password login (web/src/app/login/actions.ts).
 */
function secretMatches(supplied: string, expected: string): boolean {
  const suppliedHash = createHash("sha256").update(supplied).digest();
  const expectedHash = createHash("sha256").update(expected).digest();
  return timingSafeEqual(suppliedHash, expectedHash);
}

function bearerToken(header: string | null): string | null {
  if (!header) return null;
  const [scheme, token] = header.split(" ");
  return scheme === "Bearer" && token ? token : null;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const expected = process.env.CRON_SECRET ?? "";
  const supplied = bearerToken(request.headers.get("authorization"));
  if (!expected || !supplied || !secretMatches(supplied, expected)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const base = process.env.PORTFOY_API_URL;
  const key = process.env.PORTFOY_API_KEY;
  if (!base || !key) {
    return NextResponse.json({ error: "not_configured" }, { status: 503 });
  }

  const res = await fetch(new URL("/api/movers/scan", base), {
    method: "POST",
    headers: { "X-API-Key": key },
    cache: "no-store",
  });
  if (!res.ok) {
    return NextResponse.json({ error: "scan_failed", upstreamStatus: res.status }, { status: 502 });
  }

  return NextResponse.json({ ok: true });
}
