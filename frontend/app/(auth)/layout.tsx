import { AuthBrandPanel } from "@/components/motion/auth-brand-panel";
import { FadeIn } from "@/components/motion/primitives";

// Authentication layout (PRD Ch7.5): left brand panel, right form panel.
// Glassmorphism is permitted here only (Ch2.14).
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <AuthBrandPanel />
      <div className="flex items-center justify-center bg-background p-8">
        <FadeIn className="w-full max-w-md">{children}</FadeIn>
      </div>
    </div>
  );
}
