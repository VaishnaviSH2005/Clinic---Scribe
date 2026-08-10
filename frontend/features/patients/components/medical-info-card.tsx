"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { usePatientMedicalProfile } from "../hooks/use-patient-detail";
import { MedicalProfileDialog } from "./medical-profile-dialog";

function TagList({
  items,
  emptyLabel,
  variant,
}: {
  items: string[];
  emptyLabel: string;
  variant?: "danger";
}) {
  if (items.length === 0) return <p className="text-body text-text-secondary">{emptyLabel}</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Badge key={item} variant={variant ?? "outline"}>
          {item}
        </Badge>
      ))}
    </div>
  );
}

export function MedicalInfoCard({ patientId }: { patientId: string }) {
  const { data: profile, isLoading } = usePatientMedicalProfile(patientId);
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Medical information</CardTitle>
        <Button size="sm" variant="secondary" onClick={() => setDialogOpen(true)}>
          Edit
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <>
            <div>
              <p className="mb-1 text-caption text-text-secondary">Known allergies</p>
              <TagList
                items={profile?.known_allergies ?? []}
                emptyLabel="No known allergies."
                variant="danger"
              />
            </div>
            <div>
              <p className="mb-1 text-caption text-text-secondary">Chronic conditions</p>
              <TagList items={profile?.chronic_diseases ?? []} emptyLabel="None recorded." />
            </div>
            <div>
              <p className="mb-1 text-caption text-text-secondary">Current medications</p>
              <TagList items={profile?.current_medications ?? []} emptyLabel="None recorded." />
            </div>
            <div>
              <p className="mb-1 text-caption text-text-secondary">Previous surgeries</p>
              <TagList items={profile?.previous_surgeries ?? []} emptyLabel="None recorded." />
            </div>
            {profile?.family_history && (
              <div>
                <p className="mb-1 text-caption text-text-secondary">Family history</p>
                <p className="text-body text-text-primary">{profile.family_history}</p>
              </div>
            )}
            <div className="flex gap-6 text-body text-text-secondary">
              {profile?.height_cm && <span>Height: {profile.height_cm} cm</span>}
              {profile?.weight_kg && <span>Weight: {profile.weight_kg} kg</span>}
            </div>
          </>
        )}
      </CardContent>
      <MedicalProfileDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        patientId={patientId}
        profile={profile ?? null}
      />
    </Card>
  );
}
