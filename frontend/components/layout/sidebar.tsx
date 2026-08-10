"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { NAV_ITEMS } from "@/constants/navigation";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/store/sidebar.store";

// Permanent left sidebar (PRD Ch5.16 / Ch6.4), filtered by the current
// role's Access Control Matrix entry (Ch6.15). Below the `lg` breakpoint it
// always renders icon-only (the same collapsed visual state the manual
// toggle already produces) so it never crowds out content on tablet/mobile
// — graceful responsive behavior without a second navigation pattern.
export function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggle } = useSidebarStore();
  const { user, logout } = useAuth();

  const items = user ? NAV_ITEMS.filter((item) => item.roles.includes(user.role)) : [];
  const labelClass = collapsed ? "hidden" : "hidden lg:inline";

  return (
    <aside
      className={cn(
        "flex h-screen flex-col justify-between bg-sidebar text-white transition-[width] duration-card ease-out",
        "w-[88px]",
        collapsed ? "lg:w-[88px]" : "lg:w-[280px]",
      )}
    >
      <div>
        <div className="flex h-[72px] items-center justify-between px-4">
          <span className={cn("text-h5 font-semibold", labelClass)}>CliniScribe AI</span>
          <button
            onClick={toggle}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden rounded-md p-2 text-white/70 hover:bg-white/10 hover:text-white lg:block"
          >
            {collapsed ? (
              <PanelLeftOpen className="h-5 w-5" />
            ) : (
              <PanelLeftClose className="h-5 w-5" />
            )}
          </button>
        </div>
        <nav className="flex flex-col gap-1 px-3 py-2">
          {items.map((item) => {
            const active = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-body transition-colors duration-micro",
                  active
                    ? "bg-primary text-white"
                    : "text-white/70 hover:bg-white/10 hover:text-white",
                )}
              >
                <Icon className="h-6 w-6 shrink-0" />
                <span className={labelClass}>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="border-t border-white/10 px-3 py-4">
        {user && (
          <div className={cn("mb-2 px-3", labelClass)}>
            <p className="truncate text-body font-medium text-white">{user.name}</p>
            <p className="truncate text-caption capitalize text-white/60">
              {user.role.replace("_", " ")}
            </p>
          </div>
        )}
        <button
          onClick={() => void logout()}
          aria-label="Logout"
          className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-body text-white/70 hover:bg-white/10 hover:text-white"
        >
          <LogOut className="h-6 w-6 shrink-0" />
          <span className={labelClass}>Logout</span>
        </button>
      </div>
    </aside>
  );
}
