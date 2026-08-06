import { getCalendar } from "@/lib/api";
import { Panel } from "@/components/panel";
import { eventLabel, daysLeftText } from "@/lib/calendar-text";

export async function CalendarPanel() {
  const calendar = await getCalendar(45);
  const today = new Date();

  return (
    <Panel title="Ekonomik Takvim" subtitle="Önümüzdeki 45 gün">
      {calendar.length === 0 ? (
        <p className="text-sm text-text-faint">Yaklaşan önemli bir tarih yok.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {calendar.map((event, i) => (
            <li key={i} className="flex items-center justify-between text-sm">
              <span className="text-text">
                <span className="tabular text-text-dim">
                  {new Date(event.when).toLocaleDateString("tr-TR")}
                </span>{" "}
                — {eventLabel(event)}
              </span>
              <span className="text-xs text-text-faint">{daysLeftText(event, today)}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
