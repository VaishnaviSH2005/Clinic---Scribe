"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ROUTES } from "@/constants/routes";
import { ApiClientError } from "@/lib/api-client";

import { useAuth } from "../hooks/use-auth";
import { authService } from "../services/auth.service";
import { loginSchema, type LoginFormValues } from "../utils/schemas";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthenticated } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      const user = await authService.login(values);
      setAuthenticated(user);
      const next = searchParams.get("next") ?? ROUTES.dashboard;
      router.push(next);
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.errorCode === "RATE_LIMIT_EXCEEDED") {
          toast.error("Too many attempts. Please try again later.");
        } else {
          toast.error(error.message || "Incorrect email or password.");
        }
      } else {
        toast.error("Unable to connect to the server. Please try again.");
      }
    }
  };

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

      <FormField label="Password" htmlFor="password" error={errors.password?.message}>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            placeholder="••••••••"
            error={!!errors.password}
            className="pr-11"
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-secondary hover:text-text-primary"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        </div>
      </FormField>

      <div className="flex justify-end">
        <Link href={ROUTES.forgotPassword} className="text-body text-primary hover:underline">
          Forgot password?
        </Link>
      </div>

      <Button type="submit" loading={isSubmitting} className="w-full">
        Log in
      </Button>
    </form>
  );
}
