"use client";

import { useState, useTransition } from "react";
import { removePositionAction } from "./actions";

export function DeletePositionButton({ symbol }: { symbol: string }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleClick() {
    if (!window.confirm(`${symbol} pozisyonunu silmek istediğine emin misin?`)) {
      return;
    }
    setError(null);
    startTransition(async () => {
      const result = await removePositionAction(symbol);
      if (result.error) {
        setError(result.error);
      }
    });
  }

  return (
    <div className="flex flex-col items-end gap-0.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        className="text-xs text-text-faint transition-colors hover:text-neg disabled:opacity-50"
      >
        {pending ? "…" : "Sil"}
      </button>
      {error && <span className="text-[10px] text-neg">{error}</span>}
    </div>
  );
}
