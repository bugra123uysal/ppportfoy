import { getMacro } from "@/lib/api";
import { MacroStrip } from "@/components/macro-strip";
import { Panel } from "@/components/panel";

export async function MacroPanel() {
  const macro = await getMacro();
  return (
    <Panel title="Piyasa Ortamı">
      <MacroStrip rows={macro} />
    </Panel>
  );
}
