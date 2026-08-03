"use client";

import type { SortDirection } from "@/lib/use-sort";

// Not generic over the sort-key union: TS can't reliably infer a shared type
// parameter across several sibling elements that each pass a different
// literal `sortKey` plus a spread `{...thProps}` (the spread's `onSort`
// contravariant position drags inference to a single call site's literal).
// Plain strings sidestep that -- a typo just shows up as "no rows sorted"
// during manual testing, not worth fighting the inference for.
export function SortableTh({
  label,
  sortKey,
  activeKey,
  direction,
  onSort,
  align = "left",
  last = false,
}: {
  label: string;
  sortKey: string;
  activeKey: string;
  direction: SortDirection;
  onSort: (key: string) => void;
  align?: "left" | "right";
  last?: boolean;
}) {
  const active = sortKey === activeKey;
  return (
    <th
      className={`py-2 font-medium ${last ? "" : "pr-4"} ${align === "right" ? "text-right" : "text-left"}`}
    >
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className={`inline-flex items-center gap-1 transition-colors hover:text-text ${
          align === "right" ? "flex-row-reverse" : ""
        } ${active ? "text-text" : ""}`}
      >
        {label}
        <span className="w-2.5 text-[9px] leading-none text-accent">
          {active ? (direction === "asc" ? "▲" : "▼") : ""}
        </span>
      </button>
    </th>
  );
}
