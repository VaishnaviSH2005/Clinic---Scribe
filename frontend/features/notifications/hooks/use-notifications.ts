"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationService } from "../services/notification.service";

export function useNotifications(open: boolean) {
  return useQuery({
    queryKey: ["notifications", "list"],
    queryFn: () => notificationService.list({ page: 1, pageSize: 10 }),
    enabled: open,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationService.unreadCount(),
    refetchInterval: 30000,
  });
}

export function useNotificationMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["notifications"] });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationService.markRead(id),
    onSuccess: () => void invalidate(),
  });

  const markAllRead = useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => void invalidate(),
  });

  return { markRead, markAllRead };
}
