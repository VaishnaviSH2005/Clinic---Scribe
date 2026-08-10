"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Profile } from "@/types/auth";

import { authService } from "../services/auth.service";
import { profileUpdateSchema, type ProfileUpdateFormValues } from "../utils/schemas";

export function ProfileForm({ profile }: { profile: Profile }) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileUpdateFormValues>({
    resolver: zodResolver(profileUpdateSchema),
    defaultValues: { full_name: profile.full_name, phone: profile.phone },
  });

  const onSubmit = async (values: ProfileUpdateFormValues) => {
    try {
      await authService.updateProfile(values);
      await queryClient.invalidateQueries({ queryKey: ["auth", "profile"] });
      toast.success("Profile updated successfully.");
    } catch {
      toast.error("Unable to update your profile. Please try again.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex max-w-form flex-col gap-5">
      <FormField label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
        <Input id="full_name" error={!!errors.full_name} {...register("full_name")} />
      </FormField>
      <FormField label="Phone number" htmlFor="phone" error={errors.phone?.message}>
        <Input id="phone" error={!!errors.phone} {...register("phone")} />
      </FormField>
      <FormField label="Email" htmlFor="email">
        <Input id="email" value={profile.email} disabled readOnly />
      </FormField>
      <FormField label="Role" htmlFor="role">
        <Input
          id="role"
          value={profile.role.replace("_", " ")}
          disabled
          readOnly
          className="capitalize"
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="w-fit">
        Save changes
      </Button>
    </form>
  );
}
