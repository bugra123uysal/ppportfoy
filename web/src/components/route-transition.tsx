"use client";

import { usePathname } from "next/navigation";

// Keyed by pathname so it only remounts (and re-plays the fade) on an actual
// route change -- not when a page's own Suspense boundary swaps its skeleton
// for real content, which stays on the same pathname.
export function RouteTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div key={pathname} className="route-fade mx-auto flex max-w-6xl flex-col gap-8">
      {children}
    </div>
  );
}
