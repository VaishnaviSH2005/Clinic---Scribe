"use client";

import { useRouter } from "next/navigation";

import { GlobalSearch } from "@/features/search/components/global-search";
import { NotificationBell } from "@/features/notifications/components/notification-bell";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { ROUTES } from "@/constants/routes";

// Sticky header (PRD Ch5.17): functional global search + notification bell,
// both backed by real hospital/role-scoped data (search/notifications APIs).
export function Header() {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between gap-4 border-b border-border bg-surface px-4 sm:px-6">
      <GlobalSearch />
      <div className="flex shrink-0 items-center gap-2 sm:gap-4">
        <NotificationBell />
        <button
          onClick={() => router.push(ROUTES.profile)}
          aria-label="Your profile"
          className="bg-muted flex h-9 w-9 items-center justify-center rounded-full text-caption font-semibold text-text-secondary hover:opacity-80"
        >
          {user?.name?.charAt(0).toUpperCase() ?? "?"}
        </button>
      </div>
    </header>
  );
}
