/** Only ever redirect somewhere on this same site's own routes.
 *
 * `startsWith("/") && !startsWith("//")` alone isn't enough: browsers
 * normalize a leading `/\` the same as `//` for special schemes (WHATWG URL
 * spec), so a `from` value like `/\evil.com` would otherwise sail through
 * this check as "local" and then resolve to `https://evil.com/`.
 */
export function safeRedirectTarget(raw: string | null | undefined): string {
  const value = typeof raw === "string" ? raw : "";
  if (!value.startsWith("/")) {
    return "/";
  }
  const second = value[1];
  if (second === "/" || second === "\\") {
    return "/";
  }
  return value;
}
