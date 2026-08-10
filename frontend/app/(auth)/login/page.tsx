import { Suspense } from "react";

import { LoginForm } from "@/features/authentication/components/login-form";

export default function LoginPage() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-h3 text-text-primary">Log in to your account</h1>
        <p className="mt-1 text-body text-text-secondary">Enter your credentials to continue.</p>
      </div>
      <Suspense>
        <LoginForm />
      </Suspense>
    </div>
  );
}
