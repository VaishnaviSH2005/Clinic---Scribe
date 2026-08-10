import { apiClient } from "@/lib/api-client";
import type { AppNotification } from "@/types/notification";

export const notificationService = {
  list: (params: { page: number; pageSize: number; unreadOnly?: boolean }) =>
    apiClient.getList<AppNotification>(
      `/notifications?page=${params.page}&pageSize=${params.pageSize}&unread_only=${params.unreadOnly ?? false}`,
    ),

  unreadCount: () => apiClient.get<{ count: number }>("/notifications/unread-count"),

  markRead: (id: string) => apiClient.post<AppNotification>(`/notifications/${id}/read`),

  markAllRead: () => apiClient.post<null>("/notifications/read-all"),
};
