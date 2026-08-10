"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/date";

import { usePatientTimeline } from "../hooks/use-patient-detail";

export function PatientTimelinePanel({ patientId }: { patientId: string }) {
  const { data: events, isLoading } = usePatientTimeline(patientId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clinical timeline</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {!isLoading && events?.length === 0 && (
          <p className="text-body text-text-secondary">No timeline events yet.</p>
        )}
        {!isLoading && events && events.length > 0 && (
          <ol className="flex flex-col gap-4 border-l border-border pl-4">
            {events.map((event) => (
              <li key={event.id} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-primary" />
                <p className="text-body font-medium text-text-primary">{event.title}</p>
                {event.description && (
                  <p className="text-body text-text-secondary">{event.description}</p>
                )}
                <p className="text-caption text-text-secondary">
                  {formatDateTime(event.event_date)}
                </p>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
