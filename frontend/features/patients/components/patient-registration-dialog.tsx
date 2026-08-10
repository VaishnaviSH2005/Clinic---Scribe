"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

import { usePatientMutations } from "../hooks/use-patients";
import { patientRegistrationSchema, type PatientRegistrationFormValues } from "../utils/schemas";

const EMPTY_VALUES: PatientRegistrationFormValues = {
  full_name: "",
  date_of_birth: "",
  gender: "male",
  blood_group: "",
  mobile_number: "",
  email: "",
  aadhaar_number: "",
  emergency_contact_name: "",
  emergency_contact_number: "",
  address_line: "",
  city: "",
  state: "",
  country: "",
  pin_code: "",
};

interface PatientRegistrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRegistered?: (patientId: string) => void;
}

export function PatientRegistrationDialog({
  open,
  onOpenChange,
  onRegistered,
}: PatientRegistrationDialogProps) {
  const { register: registerMutation } = usePatientMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PatientRegistrationFormValues>({
    resolver: zodResolver(patientRegistrationSchema),
    defaultValues: EMPTY_VALUES,
  });

  useEffect(() => {
    if (open) reset(EMPTY_VALUES);
  }, [open, reset]);

  const onSubmit = (values: PatientRegistrationFormValues) => {
    const payload = {
      ...values,
      email: values.email || undefined,
      blood_group: values.blood_group || undefined,
      aadhaar_number: values.aadhaar_number || undefined,
    };
    registerMutation.mutate(payload, {
      onSuccess: (patient) => {
        onOpenChange(false);
        onRegistered?.(patient.id);
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Register patient</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-6">
          <div className="flex flex-col gap-4">
            <h3 className="text-h5 text-text-primary">Personal information</h3>
            <FormField label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
              <Input
                id="full_name"
                autoFocus
                error={!!errors.full_name}
                {...register("full_name")}
              />
            </FormField>
            <div className="grid grid-cols-3 gap-4">
              <FormField
                label="Date of birth"
                htmlFor="date_of_birth"
                error={errors.date_of_birth?.message}
              >
                <Input
                  id="date_of_birth"
                  type="date"
                  error={!!errors.date_of_birth}
                  {...register("date_of_birth")}
                />
              </FormField>
              <FormField label="Gender" htmlFor="gender" error={errors.gender?.message}>
                <Select id="gender" error={!!errors.gender} {...register("gender")}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </Select>
              </FormField>
              <FormField label="Blood group" htmlFor="blood_group">
                <Input id="blood_group" placeholder="O+" {...register("blood_group")} />
              </FormField>
            </div>
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
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Aadhaar number" htmlFor="aadhaar_number">
                <Input id="aadhaar_number" {...register("aadhaar_number")} />
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
          </div>

          <div className="flex flex-col gap-4">
            <h3 className="text-h5 text-text-primary">Address</h3>
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
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={registerMutation.isPending}>
              Register patient
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
