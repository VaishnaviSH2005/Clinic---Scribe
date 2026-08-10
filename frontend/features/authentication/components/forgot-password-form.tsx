"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { authService } from "../services/auth.service";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "../utils/schemas";

export function ForgotPasswordForm() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) });

  const onSubmit = async (values: ForgotPasswordFormValues) => {
    // Always show the same success state regardless of outcome (PRD Ch7.10
    // — prevent account enumeration); the backend already behaves this way.
    try {
      await authService.forgotPassword(values);
    } finally {
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <p className="text-body text-text-secondary">
        If an account exists for that email, password reset instructions have been sent.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      <FormField label="Email" htmlFor="email" error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoFocus
          autoComplete="email"
          placeholder="you@hospital.com"
          error={!!errors.email}
          {...register("email")}
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="w-full">
        Send reset link
      </Button>
    </form>
  );
}
