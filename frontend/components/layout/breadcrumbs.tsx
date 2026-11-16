"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { ROUTES } from "@/constants/routes";

// Breadcrumb trail (PRD Ch6.16: every page contains one). Derived from the URL so
// it can never disagree with where the user actually is. Opaque IDs in the path
// are shown as the record type ("Patient", "Report", …) instead of a UUID.
const SEGMENT_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  hospitals: "Hospitals",
  licenses: "Licenses",
  "audit-logs": "Audit Logs",
  patients: "Patients",
  appointments: "Appointments",
  consultations: "Consultations",
  reports: "Reports",
  analytics: "Analytics",
  settings: "Settings",
  profile: "Profile",
};

const DETAIL_LABELS: Record<string, string> = {
  patients: "Patient",
  consultations: "Consultation",
  reports: "Report",
};

const looksLikeId = (segment: string) => /^[0-9a-f-]{8,}$/i.test(segment);

export function Breadcrumbs() {
  const pathname = usePathname() ?? "";
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return null;

  const crumbs = segments.map((segment, index) => ({
    href: `/${segments.slice(0, index + 1).join("/")}`,
    label: looksLikeId(segment)
      ? (DETAIL_LABELS[segments[index - 1] ?? ""] ?? "Details")
      : (SEGMENT_LABELS[segment] ?? segment.replace(/-/g, " ")),
  }));
  // Always start from the Dashboard (the role's home) unless we are on it.
  const trail =
    segments[0] === "dashboard"
      ? crumbs
      : [{ href: ROUTES.dashboard, label: "Dashboard" }, ...crumbs];

  return (
    <nav aria-label="Breadcrumb" className="hidden min-w-0 md:block">
      <ol className="flex items-center gap-1.5 text-caption text-text-secondary">
        {trail.map((crumb, index) => {
          const last = index === trail.length - 1;
          return (
            <li key={crumb.href} className="flex items-center gap-1.5">
              {last ? (
                <span aria-current="page" className="font-medium text-text-primary">
                  {crumb.label}
                </span>
              ) : (
                <>
                  <Link href={crumb.href} className="hover:text-text-primary hover:underline">
                    {crumb.label}
                  </Link>
                  <ChevronRight className="h-3 w-3" aria-hidden="true" />
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
