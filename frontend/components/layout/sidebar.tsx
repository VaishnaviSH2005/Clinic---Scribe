"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { CARD_MS, EASE_OUT } from "@/components/motion/primitives";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
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
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

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
          {items.map((item, index) => {
            const active = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <motion.div
                key={item.href}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: CARD_MS, delay: index * 0.02, ease: EASE_OUT }}
              >
                <Link
                  href={item.href}
                  aria-label={item.label}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "relative flex items-center gap-3 rounded-md px-3 py-2.5 text-body transition-colors duration-micro",
                    active ? "text-white" : "text-white/70 hover:bg-white/10 hover:text-white",
                  )}
                >
                  {active && (
                    // Shared layoutId: the pill slides between items on navigation.
                    <motion.span
                      layoutId="sidebar-active-pill"
                      className="absolute inset-0 rounded-md bg-primary"
                      transition={{ duration: CARD_MS, ease: EASE_OUT }}
                    />
                  )}
                  <Icon className="relative h-6 w-6 shrink-0" />
                  <span className={cn("relative", labelClass)}>{item.label}</span>
                </Link>
              </motion.div>
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
          onClick={() => setLogoutOpen(true)}
          aria-label="Logout"
          className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-body text-white/70 hover:bg-white/10 hover:text-white"
        >
          <LogOut className="h-6 w-6 shrink-0" />
          <span className={labelClass}>Logout</span>
        </button>
      </div>
      <ConfirmDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="Log out?"
        description="You will need to sign in again to continue working."
        confirmLabel="Log out"
        loading={loggingOut}
        onConfirm={() => {
          setLoggingOut(true);
          void logout();
        }}
      />
    </aside>
  );
}
