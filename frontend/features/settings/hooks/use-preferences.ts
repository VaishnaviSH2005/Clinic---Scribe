"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { ApplicationPreferences, NotificationPreferences } from "@/types/settings";

import { preferencesService } from "../services/preferences.service";

export function useUserSettings() {
  return useQuery({
    queryKey: ["settings", "me"],
    queryFn: () => preferencesService.get(),
  });
}

export function usePreferenceMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["settings", "me"] });

  const updateNotifications = useMutation({
    mutationFn: (payload: NotificationPreferences) =>
      preferencesService.updateNotificationPreferences(payload),
    onSuccess: () => {
      toast.success("Notification preferences saved.");
      void invalidate();
    },
    onError: () => toast.error("Unable to save notification preferences."),
  });

  const updateApplication = useMutation({
    mutationFn: (payload: ApplicationPreferences) =>
      preferencesService.updateApplicationPreferences(payload),
    onSuccess: () => {
      toast.success("Application preferences saved.");
      void invalidate();
    },
    onError: () => toast.error("Unable to save application preferences."),
  });

  return { updateNotifications, updateApplication };
}
