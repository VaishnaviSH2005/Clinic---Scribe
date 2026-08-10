"use client";

import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ROUTES } from "@/constants/routes";
import { ApiClientError } from "@/lib/api-client";

import { authService } from "../services/auth.service";
import { resetPasswordSchema, type ResetPasswordFormValues } from "../utils/schemas";

export function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) });

  const onSubmit = async (values: ResetPasswordFormValues) => {
    try {
      await authService.resetPassword({ token, password: values.password });
      toast.success("Password updated successfully. Please log in.");
      router.push(ROUTES.login);
    } catch (error) {
      if (error instanceof ApiClientError && error.errorCode === "RESET_TOKEN_EXPIRED") {
        toast.error("This password reset link has expired. Please request a new one.");
      } else {
        toast.error("Unable to reset your password. Please try again.");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      <FormField label="New password" htmlFor="password" error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoFocus
          error={!!errors.password}
          {...register("password")}
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
          error={!!errors.confirmPassword}
          {...register("confirmPassword")}
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="w-full">
        Set new password
      </Button>
    </form>
  );
}
