"use client";

import { useState } from "react";

export type SortDirection = "asc" | "desc";

/**
 * Click-to-sort table state. Clicking the active column flips direction;
 * clicking a different column switches to it (defaulting to descending,
 * the more useful default for financial data -- largest first).
 */
export function useSort<T, K extends string>(
  rows: readonly T[],
  accessors: Record<K, (row: T) => number | string>,
  initialKey: K,
  initialDirection: SortDirection = "desc",
) {
  const [sortKey, setSortKey] = useState<K>(initialKey);
  const [direction, setDirection] = useState<SortDirection>(initialDirection);

  // Accepts a plain string (not K) so it drops straight into <SortableTh
  // onSort={toggle} /> without generic-inference gymnastics at the call site.
  function toggle(key: string) {
    const nextKey = key as K;
    if (nextKey === sortKey) {
      setDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(nextKey);
      setDirection("desc");
    }
  }

  const accessor = accessors[sortKey];
  const sorted = [...rows].sort((a, b) => {
    const av = accessor(a);
    const bv = accessor(b);
    const cmp =
      typeof av === "string" && typeof bv === "string"
        ? av.localeCompare(bv, "tr")
        : (av as number) - (bv as number);
    return direction === "asc" ? cmp : -cmp;
  });

  return { sorted, sortKey, direction, toggle };
}
