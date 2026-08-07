import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { COOKIE_NAME, isValidSession } from "@/lib/auth";

export function proxy(request: NextRequest) {
  const cookie = request.cookies.get(COOKIE_NAME)?.value;
  if (isValidSession(cookie)) {
    return NextResponse.next();
  }
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("from", request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    // api/cron/ (with the trailing slash -- a bare "api/cron" would also
    // match any future path merely *starting* with those characters, e.g.
    // "/api/cronjobs", silently inheriting the password-gate bypass) is
    // excluded deliberately: it's hit by an external scheduler (GitHub
    // Actions, see .github/workflows/movers-scan.yml) that has no session
    // cookie. Routes under it authenticate themselves via CRON_SECRET
    // instead -- see web/src/app/api/cron/movers-scan/route.ts.
    "/((?!login|api/cron/|_next/static|_next/image|favicon.ico|robots.txt).*)",
  ],
};
