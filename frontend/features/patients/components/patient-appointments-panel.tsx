"use client";

import { StatusBadge } from "@/components/badges/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/date";

import { usePatientAppointments } from "../hooks/use-patient-detail";

export function PatientAppointmentsPanel({ patientId }: { patientId: string }) {
  const { data: appointments, isLoading } = usePatientAppointments(patientId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Appointment history</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {!isLoading && appointments?.length === 0 && (
          <p className="text-body text-text-secondary">No appointments found.</p>
        )}
        {!isLoading && appointments && appointments.length > 0 && (
          <ul className="flex flex-col divide-y divide-border">
            {appointments.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-3">
                <p className="text-body text-text-primary">{formatDateTime(a.scheduled_at)}</p>
                <StatusBadge status={a.status} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
