import Link from "next/link";

import { ROUTES } from "@/constants/routes";

export default function RootPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background text-center">
      <h1 className="text-h2 text-text-primary">CliniScribe AI</h1>
      <p className="text-body text-text-secondary">AI That Listens. Doctors Who Decide.</p>
      <Link href={ROUTES.login} className="text-body-lg text-primary underline underline-offset-4">
        Go to Login
      </Link>
    </main>
  );
}
