import { apiClient } from "@/lib/api-client";
import type {
  ApplicationPreferences,
  NotificationPreferences,
  UserSettings,
} from "@/types/settings";

export const preferencesService = {
  get: () => apiClient.get<UserSettings>("/settings/me"),

  updateNotificationPreferences: (payload: NotificationPreferences) =>
    apiClient.patch<NotificationPreferences>("/settings/me/notification-preferences", payload),

  updateApplicationPreferences: (payload: ApplicationPreferences) =>
    apiClient.patch<ApplicationPreferences>("/settings/me/application-preferences", payload),
};
