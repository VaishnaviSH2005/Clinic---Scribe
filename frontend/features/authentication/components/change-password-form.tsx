"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiClientError } from "@/lib/api-client";

import { authService } from "../services/auth.service";
import { changePasswordSchema, type ChangePasswordFormValues } from "../utils/schemas";

export function ChangePasswordForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormValues>({ resolver: zodResolver(changePasswordSchema) });

  const onSubmit = async (values: ChangePasswordFormValues) => {
    try {
      await authService.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      toast.success("Password changed successfully. Other sessions have been signed out.");
      reset();
    } catch (error) {
      if (error instanceof ApiClientError && error.errorCode === "INCORRECT_PASSWORD") {
        toast.error("Current password is incorrect.");
      } else {
        toast.error("Unable to change your password. Please try again.");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex max-w-form flex-col gap-5">
      <FormField
        label="Current password"
        htmlFor="currentPassword"
        error={errors.currentPassword?.message}
      >
        <Input
          id="currentPassword"
          type="password"
          autoComplete="current-password"
          error={!!errors.currentPassword}
          {...register("currentPassword")}
        />
      </FormField>
      <FormField label="New password" htmlFor="newPassword" error={errors.newPassword?.message}>
        <Input
          id="newPassword"
          type="password"
          autoComplete="new-password"
          error={!!errors.newPassword}
          {...register("newPassword")}
        />
      </FormField>
      <FormField
        label="Confirm new password"
        htmlFor="confirmPassword"
        error={errors.confirmPassword?.message}
      >
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          error={!!errors.confirmPassword}
          {...register("confirmPassword")}
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="w-fit">
        Change password
      </Button>
    </form>
  );
}
