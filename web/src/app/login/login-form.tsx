"use client";

import { useActionState } from "react";
import { login } from "./actions";

export function LoginForm({ from }: { from: string }) {
  const [state, action, pending] = useActionState(login, { error: false });

  return (
    <form action={action} className="flex w-full flex-col gap-4">
      <input type="hidden" name="from" value={from} />
      <div className="flex flex-col gap-2">
        <label htmlFor="password" className="text-sm text-text-dim">
          Şifre
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoFocus
          required
          className="tabular rounded-lg border border-border bg-surface-2 px-4 py-3 text-text outline-none transition-colors focus:border-accent"
        />
      </div>
      {state.error && (
        <p className="text-sm text-neg">Şifre yanlış. Tekrar dene.</p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="mt-2 rounded-lg bg-accent px-4 py-3 font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Kontrol ediliyor…" : "Giriş yap"}
      </button>
    </form>
  );
}
