"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/nav";
import { logout } from "@/app/logout/actions";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-3 px-6 py-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-soft text-accent">
          ◆
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight text-text">Portföy</p>
          <p className="text-xs leading-tight text-text-faint">Takip Merkezi</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-sm transition-colors ${
                active
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-transparent text-text-dim hover:bg-surface-2 hover:text-text"
              }`}
            >
              <span className="w-4 text-center text-xs">{item.glyph}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border px-3 py-4">
        <form action={logout}>
          <button
            type="submit"
            className="w-full rounded-lg px-3 py-2 text-left text-xs text-text-faint transition-colors hover:bg-surface-2 hover:text-text-dim"
          >
            Çıkış yap
          </button>
        </form>
        <p className="mt-3 px-3 text-[11px] leading-snug text-text-faint">
          Eğitim amaçlıdır, yatırım tavsiyesi değildir.
        </p>
      </div>
    </aside>
  );
}
