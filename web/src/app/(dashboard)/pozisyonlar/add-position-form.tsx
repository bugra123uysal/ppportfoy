"use client";

import { useActionState } from "react";
import { addPositionAction, type FormState } from "./actions";

const initialState: FormState = { error: null };

export function AddPositionForm() {
  const [state, action, pending] = useActionState(addPositionAction, initialState);

  return (
    <form action={action} className="flex flex-wrap items-end gap-3">
      <Field label="Sembol" htmlFor="symbol">
        <input
          id="symbol"
          name="symbol"
          required
          placeholder="AAPL"
          className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <Field label="Adet" htmlFor="quantity">
        <input
          id="quantity"
          name="quantity"
          type="number"
          step="any"
          min={0}
          required
          className="tabular w-24 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <Field label="Ort. Maliyet" htmlFor="avg_cost">
        <input
          id="avg_cost"
          name="avg_cost"
          type="number"
          step="any"
          min={0}
          required
          className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <Field label="Not (opsiyonel)" htmlFor="notes">
        <input
          id="notes"
          name="notes"
          className="w-40 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Ekleniyor…" : "Ekle"}
      </button>
      {state.error && <p className="w-full text-xs text-neg">{state.error}</p>}
    </form>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-xs text-text-faint">
        {label}
      </label>
      {children}
    </div>
  );
}
