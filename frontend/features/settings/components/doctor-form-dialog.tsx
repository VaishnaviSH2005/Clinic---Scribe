"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Department } from "@/types/department";
import type { StaffUser } from "@/types/user";

import { doctorFormSchema, type DoctorFormValues } from "../utils/schemas";

interface DoctorFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  doctor?: StaffUser | null;
  departments: Department[];
  loading?: boolean;
  onSubmit: (values: DoctorFormValues) => void;
}

export function DoctorFormDialog({
  open,
  onOpenChange,
  doctor,
  departments,
  loading,
  onSubmit,
}: DoctorFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DoctorFormValues>({ resolver: zodResolver(doctorFormSchema) });

  useEffect(() => {
    if (open) {
      reset(
        doctor
          ? {
              full_name: doctor.full_name,
              email: doctor.email,
              phone: doctor.phone,
              department_id: doctor.department_id ?? "",
              qualification: doctor.qualification ?? "",
              specialization: doctor.specialization ?? "",
              medical_registration_number: doctor.medical_registration_number ?? "",
            }
          : {
              full_name: "",
              email: "",
              phone: "",
              department_id: "",
              qualification: "",
              specialization: "",
              medical_registration_number: "",
            },
      );
    }
  }, [open, doctor, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{doctor ? "Edit doctor" : "Add doctor"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
            <Input id="full_name" autoFocus error={!!errors.full_name} {...register("full_name")} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Email" htmlFor="email" error={errors.email?.message}>
              <Input
                id="email"
                type="email"
                disabled={!!doctor}
                error={!!errors.email}
                {...register("email")}
              />
            </FormField>
            <FormField label="Phone" htmlFor="phone" error={errors.phone?.message}>
              <Input id="phone" error={!!errors.phone} {...register("phone")} />
            </FormField>
          </div>
          <FormField
            label="Department"
            htmlFor="department_id"
            error={errors.department_id?.message}
          >
            <Select
              id="department_id"
              error={!!errors.department_id}
              {...register("department_id")}
            >
              <option value="">Select a department</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Qualification" htmlFor="qualification">
              <Input id="qualification" {...register("qualification")} />
            </FormField>
            <FormField label="Specialization" htmlFor="specialization">
              <Input id="specialization" {...register("specialization")} />
            </FormField>
          </div>
          <FormField label="Medical registration number" htmlFor="medical_registration_number">
            <Input id="medical_registration_number" {...register("medical_registration_number")} />
          </FormField>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {doctor ? "Save changes" : "Create doctor"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
