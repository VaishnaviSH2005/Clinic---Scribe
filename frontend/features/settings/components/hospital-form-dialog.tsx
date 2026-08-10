"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Hospital } from "@/types/hospital";

import { hospitalFormSchema, type HospitalFormValues } from "../utils/schemas";

interface HospitalFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  hospital?: Hospital | null;
  loading?: boolean;
  onSubmit: (values: HospitalFormValues) => void;
  onUploadLogo?: (file: File) => void;
  logoUploading?: boolean;
}

export function HospitalFormDialog({
  open,
  onOpenChange,
  hospital,
  loading,
  onSubmit,
  onUploadLogo,
  logoUploading,
}: HospitalFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<HospitalFormValues>({ resolver: zodResolver(hospitalFormSchema) });

  useEffect(() => {
    if (open) {
      reset(
        hospital
          ? {
              name: hospital.name,
              registration_number: hospital.registration_number,
              email: hospital.email,
              phone: hospital.phone,
              address_line: hospital.address_line ?? "",
              city: hospital.city ?? "",
              state: hospital.state ?? "",
              country: hospital.country ?? "",
            }
          : {
              name: "",
              registration_number: "",
              email: "",
              phone: "",
              address_line: "",
              city: "",
              state: "",
              country: "",
            },
      );
    }
  }, [open, hospital, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{hospital ? "Edit hospital" : "Add hospital"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Hospital name" htmlFor="name" error={errors.name?.message}>
            <Input id="name" error={!!errors.name} {...register("name")} />
          </FormField>
          <FormField
            label="Registration number"
            htmlFor="registration_number"
            error={errors.registration_number?.message}
          >
            <Input
              id="registration_number"
              disabled={!!hospital}
              error={!!errors.registration_number}
              {...register("registration_number")}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Email" htmlFor="email" error={errors.email?.message}>
              <Input id="email" type="email" error={!!errors.email} {...register("email")} />
            </FormField>
            <FormField label="Phone" htmlFor="phone" error={errors.phone?.message}>
              <Input id="phone" error={!!errors.phone} {...register("phone")} />
            </FormField>
          </div>
          {hospital && onUploadLogo && (
            <FormField label="Logo" htmlFor="logo">
              <div className="flex items-center gap-3">
                {hospital.logo_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={hospital.logo_url}
                    alt={`${hospital.name} logo`}
                    className="h-10 w-10 rounded object-cover"
                  />
                )}
                <Input
                  id="logo"
                  type="file"
                  accept="image/jpeg,image/png"
                  disabled={logoUploading}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) onUploadLogo(file);
                  }}
                />
              </div>
            </FormField>
          )}
          <FormField label="Address" htmlFor="address_line">
            <Input id="address_line" {...register("address_line")} />
          </FormField>
          <div className="grid grid-cols-3 gap-4">
            <FormField label="City" htmlFor="city">
              <Input id="city" {...register("city")} />
            </FormField>
            <FormField label="State" htmlFor="state">
              <Input id="state" {...register("state")} />
            </FormField>
            <FormField label="Country" htmlFor="country">
              <Input id="country" {...register("country")} />
            </FormField>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {hospital ? "Save changes" : "Create hospital"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
