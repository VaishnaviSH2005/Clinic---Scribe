import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/features/authentication/components/protected-route";

// Application shell (PRD Ch5.5): fixed sidebar, sticky header, independently
// scrolling content, gated behind the Protected Route Guard (Ch19).
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-content">{children}</div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
