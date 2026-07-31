import { LoginForm } from "./login-form";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string }>;
}) {
  const { from } = await searchParams;

  return (
    <main className="flex flex-1 items-center justify-center px-6">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-2xl shadow-black/40">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-soft text-accent">
            ◆
          </div>
          <div>
            <p className="text-sm font-medium text-text">Portföy Takip Merkezi</p>
            <p className="text-xs text-text-faint">Özel panel</p>
          </div>
        </div>
        <LoginForm from={from && from.startsWith("/") ? from : "/"} />
      </div>
    </main>
  );
}
