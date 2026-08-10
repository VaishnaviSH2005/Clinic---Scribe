"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { usePatient } from "../hooks/use-patient-detail";
import { MedicalInfoCard } from "./medical-info-card";
import { PatientAppointmentsPanel } from "./patient-appointments-panel";
import { PatientDocumentsPanel } from "./patient-documents-panel";
import { PatientHeader } from "./patient-header";
import { PatientTimelinePanel } from "./patient-timeline-panel";

export function PatientDetailView({ patientId }: { patientId: string }) {
  const { data: patient, isLoading, isError } = usePatient(patientId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !patient) {
    return (
      <Card>
        <CardContent className="py-10 text-center">
          <p className="text-body-lg font-medium text-text-primary">Patient not found</p>
          <p className="mt-1 text-body text-text-secondary">
            The requested patient record could not be located.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <PatientHeader patient={patient} />

      <Tabs defaultValue="medical">
        <TabsList>
          <TabsTrigger value="medical">Medical Summary</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="appointments">Appointments</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="medical">
          <MedicalInfoCard patientId={patient.id} />
        </TabsContent>
        <TabsContent value="timeline">
          <PatientTimelinePanel patientId={patient.id} />
        </TabsContent>
        <TabsContent value="appointments">
          <PatientAppointmentsPanel patientId={patient.id} />
        </TabsContent>
        <TabsContent value="documents">
          <PatientDocumentsPanel patientId={patient.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
