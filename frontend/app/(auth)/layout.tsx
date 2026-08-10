// Authentication layout (PRD Ch7.5): left brand panel, right form panel.
// Glassmorphism is permitted here only (Ch2.14).
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-sidebar p-12 text-white lg:flex">
        <div>
          <span className="text-h4 font-semibold">CliniScribe AI</span>
        </div>
        <div className="space-y-3">
          <p className="text-h2 font-semibold">AI That Listens.</p>
          <p className="text-h2 font-semibold text-white/70">Doctors Who Decide.</p>
        </div>
        <p className="text-caption text-white/50">Version 1.0 — CliniScribe AI</p>
      </div>
      <div className="flex items-center justify-center bg-background p-8">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
