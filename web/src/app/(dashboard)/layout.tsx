import { Sidebar } from "@/components/sidebar";

// Every page under this layout fetches live portfolio/market data through the
// "api" service binding, which only resolves at request time (never during
// the build's static-generation pass) -- so none of this can be prerendered.
export const dynamic = "force-dynamic";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-1">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden px-8 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">{children}</div>
      </main>
    </div>
  );
}
