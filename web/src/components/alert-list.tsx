import type { Alert } from "@/lib/api";
import { alertText, SEVERITY_LABEL } from "@/lib/alert-text";

const SEVERITY_STYLE: Record<Alert["severity"], string> = {
  crit: "border-l-neg bg-neg-soft/40",
  warn: "border-l-accent bg-accent-soft/40",
  info: "border-l-border-strong bg-surface-2",
};

const SEVERITY_TEXT: Record<Alert["severity"], string> = {
  crit: "text-neg",
  warn: "text-accent",
  info: "text-text-faint",
};

export function AlertList({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return (
      <p className="text-sm text-text-faint">Şu anda aktif bir uyarı yok.</p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {alerts.map((alert, i) => (
        <div
          key={`${alert.key}-${i}`}
          className={`flex items-start gap-3 rounded-lg border-l-4 px-4 py-3 ${SEVERITY_STYLE[alert.severity]}`}
        >
          <span
            className={`mt-0.5 shrink-0 text-[10px] font-bold tracking-wide ${SEVERITY_TEXT[alert.severity]}`}
          >
            {SEVERITY_LABEL[alert.severity]}
          </span>
          <p className="text-sm text-text">{alertText(alert)}</p>
        </div>
      ))}
    </div>
  );
}
