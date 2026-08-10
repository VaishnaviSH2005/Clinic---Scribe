"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Bell, CheckCheck } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ROUTES } from "@/constants/routes";
import { formatDateTime } from "@/lib/date";

import {
  useNotificationMutations,
  useNotifications,
  useUnreadCount,
} from "../hooks/use-notifications";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { data: unread } = useUnreadCount();
  const { data: notifications, isLoading } = useNotifications(open);
  const { markRead, markAllRead } = useNotificationMutations();

  const count = unread?.count ?? 0;

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Notifications${count > 0 ? ` (${count} unread)` : ""}`}
          className="hover:bg-muted relative rounded-md p-2 text-text-secondary"
        >
          <Bell className="h-5 w-5" />
          {count > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold text-white">
              {count > 9 ? "9+" : count}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-[400px] w-[360px] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <span className="text-body font-medium text-text-primary">Notifications</span>
          {count > 0 && (
            <button
              onClick={() => markAllRead.mutate()}
              className="flex items-center gap-1 text-caption text-primary hover:underline"
            >
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </button>
          )}
        </div>

        {isLoading && (
          <p className="px-4 py-6 text-center text-body text-text-secondary">Loading…</p>
        )}

        {!isLoading && (notifications?.data.length ?? 0) === 0 && (
          <p className="px-4 py-6 text-center text-body text-text-secondary">
            You&apos;re all caught up.
          </p>
        )}

        {!isLoading &&
          notifications?.data.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                if (!n.is_read) markRead.mutate(n.id);
                setOpen(false);
                if (n.type === "report_generated" && n.reference_id) {
                  router.push(`${ROUTES.reports}/${n.reference_id}`);
                } else if (n.reference_id) {
                  router.push(`${ROUTES.consultations}/${n.reference_id}`);
                }
              }}
              className="hover:bg-muted flex w-full flex-col gap-0.5 border-b border-border px-4 py-3 text-left last:border-b-0"
            >
              <span className="flex items-center gap-2">
                {!n.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />}
                <span className="text-body font-medium text-text-primary">{n.title}</span>
              </span>
              {n.message && <span className="text-caption text-text-secondary">{n.message}</span>}
              <span className="text-caption text-text-secondary">
                {formatDateTime(n.created_at)}
              </span>
            </button>
          ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
