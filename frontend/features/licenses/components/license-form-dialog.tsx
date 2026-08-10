"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Hospital } from "@/types/hospital";

import { licenseFormSchema, type LicenseFormValues } from "../utils/schemas";

interface LicenseFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  hospitals: Hospital[];
  loading?: boolean;
  onSubmit: (values: LicenseFormValues) => void;
}

export function LicenseFormDialog({
  open,
  onOpenChange,
  hospitals,
  loading,
  onSubmit,
}: LicenseFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LicenseFormValues>({
    resolver: zodResolver(licenseFormSchema),
    defaultValues: { status: "trial" },
  });

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) reset({ hospital_id: "", plan_name: "", status: "trial", starts_at: "", expires_at: "" });
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add license</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Hospital" htmlFor="hospital_id" error={errors.hospital_id?.message}>
            <Select id="hospital_id" error={!!errors.hospital_id} {...register("hospital_id")}>
              <option value="">Select a hospital</option>
              {hospitals.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Plan name" htmlFor="plan_name" error={errors.plan_name?.message}>
            <Input id="plan_name" error={!!errors.plan_name} {...register("plan_name")} />
          </FormField>
          <FormField label="Status" htmlFor="status" error={errors.status?.message}>
            <Select id="status" error={!!errors.status} {...register("status")}>
              <option value="trial">Trial</option>
              <option value="active">Active</option>
              <option value="expired">Expired</option>
              <option value="cancelled">Cancelled</option>
            </Select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Starts on" htmlFor="starts_at" error={errors.starts_at?.message}>
              <Input id="starts_at" type="date" error={!!errors.starts_at} {...register("starts_at")} />
            </FormField>
            <FormField label="Expires on" htmlFor="expires_at" error={errors.expires_at?.message}>
              <Input id="expires_at" type="date" error={!!errors.expires_at} {...register("expires_at")} />
            </FormField>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              Create license
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
