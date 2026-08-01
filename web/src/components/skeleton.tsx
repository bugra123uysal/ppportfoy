export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-surface-2 ${className}`} />;
}

// Route-level `loading.tsx` fallback -- shown instantly on navigation while
// the Server Component's data fetches resolve, so a page change never feels
// like a dead click. `panels` roughly matches the target page's Panel count
// so the swap-in on arrival doesn't jump around too much.
export function PageSkeleton({ panels = 2 }: { panels?: number }) {
  return (
    <>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-3 w-72" />
      </div>
      {Array.from({ length: panels }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-surface p-6">
          <Skeleton className="mb-4 h-4 w-32" />
          <Skeleton className="h-32 w-full" />
        </div>
      ))}
    </>
  );
}
