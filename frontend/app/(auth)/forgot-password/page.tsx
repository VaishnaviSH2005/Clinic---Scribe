import Link from "next/link";

import { ROUTES } from "@/constants/routes";
import { ForgotPasswordForm } from "@/features/authentication/components/forgot-password-form";

export default function ForgotPasswordPage() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-h3 text-text-primary">Forgot your password?</h1>
        <p className="mt-1 text-body text-text-secondary">
          Enter your email and we&apos;ll send you a link to reset it.
        </p>
      </div>
      <ForgotPasswordForm />
      <Link href={ROUTES.login} className="text-body text-primary hover:underline">
        Back to login
      </Link>
    </div>
  );
}
