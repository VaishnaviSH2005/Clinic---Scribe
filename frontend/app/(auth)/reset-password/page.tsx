import Link from "next/link";

import { ROUTES } from "@/constants/routes";
import { ResetPasswordForm } from "@/features/authentication/components/reset-password-form";

interface ResetPasswordPageProps {
  searchParams: Promise<{ token?: string }>;
}

export default async function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const { token } = await searchParams;

  if (!token) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-h3 text-text-primary">Invalid reset link</h1>
        <p className="text-body text-text-secondary">
          This password reset link is missing its token. Please request a new one.
        </p>
        <Link href={ROUTES.forgotPassword} className="text-body text-primary hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-h3 text-text-primary">Set a new password</h1>
        <p className="mt-1 text-body text-text-secondary">
          Choose a strong password for your account.
        </p>
      </div>
      <ResetPasswordForm token={token} />
    </div>
  );
}
