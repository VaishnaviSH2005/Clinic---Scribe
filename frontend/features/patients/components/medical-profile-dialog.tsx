"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { MedicalProfile } from "@/types/patient";

import { usePatientDetailMutations } from "../hooks/use-patient-detail";
import { medicalProfileSchema, type MedicalProfileFormValues } from "../utils/schemas";

interface MedicalProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patientId: string;
  profile: MedicalProfile | null;
}

const listToText = (values: string[]) => values.join(", ");
const textToList = (value?: string) =>
  value
    ? value
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean)
    : [];

export function MedicalProfileDialog({
  open,
  onOpenChange,
  patientId,
  profile,
}: MedicalProfileDialogProps) {
  const { updateMedicalProfile } = usePatientDetailMutations(patientId);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MedicalProfileFormValues>({ resolver: zodResolver(medicalProfileSchema) });

  useEffect(() => {
    if (open) {
      reset({
        known_allergies: listToText(profile?.known_allergies ?? []),
        chronic_diseases: listToText(profile?.chronic_diseases ?? []),
        current_medications: listToText(profile?.current_medications ?? []),
        previous_surgeries: listToText(profile?.previous_surgeries ?? []),
        family_history: profile?.family_history ?? "",
        lifestyle_smoking: profile?.lifestyle_smoking ?? false,
        lifestyle_alcohol: profile?.lifestyle_alcohol ?? false,
        lifestyle_tobacco: profile?.lifestyle_tobacco ?? false,
        height_cm: profile?.height_cm ? String(profile.height_cm) : "",
        weight_kg: profile?.weight_kg ? String(profile.weight_kg) : "",
      });
    }
  }, [open, profile, reset]);

  const onSubmit = (values: MedicalProfileFormValues) => {
    updateMedicalProfile.mutate(
      {
        known_allergies: textToList(values.known_allergies),
        chronic_diseases: textToList(values.chronic_diseases),
        current_medications: textToList(values.current_medications),
        previous_surgeries: textToList(values.previous_surgeries),
        family_history: values.family_history || null,
        lifestyle_smoking: values.lifestyle_smoking ?? null,
        lifestyle_alcohol: values.lifestyle_alcohol ?? null,
        lifestyle_tobacco: values.lifestyle_tobacco ?? null,
        height_cm: values.height_cm ? Number(values.height_cm) : null,
        weight_kg: values.weight_kg ? Number(values.weight_kg) : null,
      },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Medical information</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField
            label="Known allergies (comma-separated)"
            htmlFor="known_allergies"
            error={errors.known_allergies?.message}
          >
            <Input id="known_allergies" {...register("known_allergies")} />
          </FormField>
          <FormField label="Chronic diseases (comma-separated)" htmlFor="chronic_diseases">
            <Input id="chronic_diseases" {...register("chronic_diseases")} />
          </FormField>
          <FormField label="Current medications (comma-separated)" htmlFor="current_medications">
            <Input id="current_medications" {...register("current_medications")} />
          </FormField>
          <FormField label="Previous surgeries (comma-separated)" htmlFor="previous_surgeries">
            <Input id="previous_surgeries" {...register("previous_surgeries")} />
          </FormField>
          <FormField label="Family history" htmlFor="family_history">
            <Input id="family_history" {...register("family_history")} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Height (cm)" htmlFor="height_cm">
              <Input id="height_cm" type="number" step="0.1" {...register("height_cm")} />
            </FormField>
            <FormField label="Weight (kg)" htmlFor="weight_kg">
              <Input id="weight_kg" type="number" step="0.1" {...register("weight_kg")} />
            </FormField>
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-body text-text-primary">
              <input type="checkbox" className="h-4 w-4" {...register("lifestyle_smoking")} />
              Smoking
            </label>
            <label className="flex items-center gap-2 text-body text-text-primary">
              <input type="checkbox" className="h-4 w-4" {...register("lifestyle_alcohol")} />
              Alcohol
            </label>
            <label className="flex items-center gap-2 text-body text-text-primary">
              <input type="checkbox" className="h-4 w-4" {...register("lifestyle_tobacco")} />
              Tobacco
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={updateMedicalProfile.isPending}>
              Save changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
