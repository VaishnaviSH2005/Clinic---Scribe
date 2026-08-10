"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { StaffUser } from "@/types/user";

import { receptionistFormSchema, type ReceptionistFormValues } from "../utils/schemas";

interface ReceptionistFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  receptionist?: StaffUser | null;
  loading?: boolean;
  onSubmit: (values: ReceptionistFormValues) => void;
}

export function ReceptionistFormDialog({
  open,
  onOpenChange,
  receptionist,
  loading,
  onSubmit,
}: ReceptionistFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReceptionistFormValues>({ resolver: zodResolver(receptionistFormSchema) });

  useEffect(() => {
    if (open) {
      reset(
        receptionist
          ? {
              full_name: receptionist.full_name,
              email: receptionist.email,
              phone: receptionist.phone,
            }
          : { full_name: "", email: "", phone: "" },
      );
    }
  }, [open, receptionist, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{receptionist ? "Edit receptionist" : "Add receptionist"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
            <Input id="full_name" autoFocus error={!!errors.full_name} {...register("full_name")} />
          </FormField>
          <FormField label="Email" htmlFor="email" error={errors.email?.message}>
            <Input
              id="email"
              type="email"
              disabled={!!receptionist}
              error={!!errors.email}
              {...register("email")}
            />
          </FormField>
          <FormField label="Phone" htmlFor="phone" error={errors.phone?.message}>
            <Input id="phone" error={!!errors.phone} {...register("phone")} />
          </FormField>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {receptionist ? "Save changes" : "Create receptionist"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
