"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Patient } from "@/types/patient";

import { usePatientDetailMutations } from "../hooks/use-patient-detail";
import { patientEditSchema, type PatientEditFormValues } from "../utils/schemas";

interface PatientEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient: Patient;
}

export function PatientEditDialog({ open, onOpenChange, patient }: PatientEditDialogProps) {
  const { updatePatient } = usePatientDetailMutations(patient.id);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PatientEditFormValues>({ resolver: zodResolver(patientEditSchema) });

  useEffect(() => {
    if (open) {
      reset({
        mobile_number: patient.mobile_number,
        email: patient.email ?? "",
        address_line: patient.address_line ?? "",
        city: patient.city ?? "",
        state: patient.state ?? "",
        country: patient.country ?? "",
        pin_code: patient.pin_code ?? "",
        emergency_contact_name: patient.emergency_contact_name ?? "",
        emergency_contact_number: patient.emergency_contact_number ?? "",
      });
    }
  }, [open, patient, reset]);

  const onSubmit = (values: PatientEditFormValues) => {
    updatePatient.mutate(
      { ...values, email: values.email || undefined },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit patient details</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Mobile number"
              htmlFor="mobile_number"
              error={errors.mobile_number?.message}
            >
              <Input
                id="mobile_number"
                error={!!errors.mobile_number}
                {...register("mobile_number")}
              />
            </FormField>
            <FormField label="Email" htmlFor="email" error={errors.email?.message}>
              <Input id="email" type="email" error={!!errors.email} {...register("email")} />
            </FormField>
          </div>
          <FormField label="Address" htmlFor="address_line">
            <Input id="address_line" {...register("address_line")} />
          </FormField>
          <div className="grid grid-cols-4 gap-4">
            <FormField label="City" htmlFor="city">
              <Input id="city" {...register("city")} />
            </FormField>
            <FormField label="State" htmlFor="state">
              <Input id="state" {...register("state")} />
            </FormField>
            <FormField label="Country" htmlFor="country">
              <Input id="country" {...register("country")} />
            </FormField>
            <FormField label="PIN code" htmlFor="pin_code">
              <Input id="pin_code" {...register("pin_code")} />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Emergency contact name" htmlFor="emergency_contact_name">
              <Input id="emergency_contact_name" {...register("emergency_contact_name")} />
            </FormField>
            <FormField label="Emergency contact number" htmlFor="emergency_contact_number">
              <Input id="emergency_contact_number" {...register("emergency_contact_number")} />
            </FormField>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={updatePatient.isPending}>
              Save changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
