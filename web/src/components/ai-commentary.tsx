// Renders the Nemotron AI narration attached to a panel's payload -- a
// "ne oldu -> neden -> ders" explanation over numbers the panel already
// shows, never a new data source. Absent whenever NVIDIA_API_KEY isn't
// configured or the call failed -- every caller must keep working without
// it, so this renders nothing rather than an error state.
export function AiCommentary({ text }: { text: string | null }) {
  if (!text) return null;

  return (
    <div className="rounded-lg border border-accent/25 bg-accent-soft p-4">
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-accent">
        Eğitici Yorum · Nemotron AI
      </p>
      <p className="whitespace-pre-line text-sm leading-relaxed text-text-dim">{text}</p>
    </div>
  );
}
