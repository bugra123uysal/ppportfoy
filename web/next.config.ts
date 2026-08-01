import type { NextConfig } from "next";

// No CSP script-src here: this app has no user-generated HTML rendering
// path (verified in security review -- no dangerouslySetInnerHTML anywhere,
// news links are validated http(s)-only server-side and rendered as plain
// hrefs), and a hand-rolled script-src risks breaking Next's own hydration
// without nonce wiring. These headers cover the standard, low-risk baseline
// (clickjacking on the password-gated login page, MIME sniffing, referrer
// leakage) without touching script execution policy.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
