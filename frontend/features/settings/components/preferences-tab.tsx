"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { usePreferenceMutations, useUserSettings } from "@/features/settings/hooks/use-preferences";
import type { ApplicationPreferences, NotificationPreferences } from "@/types/settings";

const NOTIFICATION_LABELS: Record<keyof NotificationPreferences, string> = {
  ai_processing_complete: "AI processing complete",
  report_generated: "Report generated",
  consultation_pending: "Consultation awaiting review",
};

export function PreferencesTab() {
  const { data, isLoading, isError } = useUserSettings();
  const { updateNotifications, updateApplication } = usePreferenceMutations();

  const [notifications, setNotifications] = useState<NotificationPreferences | null>(null);
  const [application, setApplication] = useState<ApplicationPreferences | null>(null);

  useEffect(() => {
    if (data) {
      setNotifications(data.notification_preferences);
      setApplication(data.application_preferences);
    }
  }, [data]);

  if (isLoading) {
    return (
      <div className="max-w-form space-y-4">
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
      </div>
    );
  }

  if (isError || !notifications || !application) {
    return <p className="text-body text-danger">Unable to load preferences. Please try again.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Notification preferences</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {(Object.keys(NOTIFICATION_LABELS) as (keyof NotificationPreferences)[]).map((key) => (
            <label key={key} className="flex items-center justify-between gap-4 py-1">
              <span className="text-body text-text-primary">{NOTIFICATION_LABELS[key]}</span>
              <input
                type="checkbox"
                checked={notifications[key]}
                onChange={(e) => setNotifications({ ...notifications, [key]: e.target.checked })}
                className="h-5 w-5 rounded border-border accent-primary"
              />
            </label>
          ))}
          <Button
            size="sm"
            className="self-start"
            loading={updateNotifications.isPending}
            onClick={() => updateNotifications.mutate(notifications)}
          >
            Save notification preferences
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Application preferences</CardTitle>
        </CardHeader>
        <CardContent className="flex max-w-form flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-caption font-medium text-text-secondary">
              Default dashboard view
            </label>
            <Select
              value={application.default_dashboard_view}
              onChange={(e) =>
                setApplication({ ...application, default_dashboard_view: e.target.value })
              }
            >
              <option value="summary">Summary</option>
              <option value="detailed">Detailed</option>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-caption font-medium text-text-secondary">Items per page</label>
            <Select
              value={String(application.items_per_page)}
              onChange={(e) =>
                setApplication({ ...application, items_per_page: Number(e.target.value) })
              }
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </Select>
          </div>
          <Button
            size="sm"
            className="self-start"
            loading={updateApplication.isPending}
            onClick={() => updateApplication.mutate(application)}
          >
            Save application preferences
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
