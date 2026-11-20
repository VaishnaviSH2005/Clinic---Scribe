"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { AlertTriangle, BarChart3, CalendarRange, ShieldCheck } from "lucide-react";

import { FadeIn } from "@/components/motion/primitives";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalytics } from "@/features/analytics/hooks/use-analytics";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { cn } from "@/lib/utils";

// recharts is a large dependency used only on this page — dynamically
// imported so it never ships in the shared bundle for every other route.
const AnalyticsCharts = dynamic(
  () => import("@/features/analytics/components/analytics-charts").then((m) => m.AnalyticsCharts),
  { ssr: false, loading: () => <DashboardSkeleton /> },
);

const PRESETS = [
  { label: "7 days", days: 6 },
  { label: "30 days", days: 29 },
  { label: "90 days", days: 89 },
];

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-36 w-full rounded-card" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Skeleton className="h-80 w-full rounded-card lg:col-span-2" />
        <Skeleton className="h-80 w-full rounded-card" />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  // Super Admin sees platform-wide aggregate counts only (PRD Ch6.3), never one hospital's internals.
  const isPlatform = user?.role === "super_admin";
  const isDoctor = user?.role === "doctor";
  const [dateFrom, setDateFrom] = useState(isoDaysAgo(29));
  const [dateTo, setDateTo] = useState(isoDaysAgo(0));
  const { data, isLoading, isError } = useAnalytics({ dateFrom, dateTo });

  const subtitle = isPlatform
    ? "Platform-wide activity across all hospitals (aggregate counts only)."
    : isDoctor
      ? "Your personal consultation activity and AI documentation outcomes."
      : "Operational insights, patient growth and consultation trends for your hospital.";

  return (
    <div className="flex flex-col gap-6">
      <FadeIn>
        <div className="relative overflow-hidden rounded-card bg-gradient-to-br from-primary via-secondary to-accent p-6 text-white shadow-level-3 sm:p-8">
          <div className="pointer-events-none absolute -right-10 -top-16 h-56 w-56 rounded-full bg-white/10 blur-2xl" />
          <div className="pointer-events-none absolute -bottom-20 left-1/3 h-56 w-56 rounded-full bg-accent/40 blur-3xl" />
          <BarChart3 className="pointer-events-none absolute -bottom-6 right-6 h-40 w-40 text-white/10" />

          <div className="relative flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-md">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-caption font-medium backdrop-blur">
                <ShieldCheck className="h-3.5 w-3.5" />
                {isPlatform ? "Platform view" : isDoctor ? "Doctor view" : "Hospital view"}
              </span>
              <h1 className="mt-3 text-h1 text-white">Analytics</h1>
              <p className="mt-2 text-body-lg text-white/85">{subtitle}</p>
            </div>

            <div className="flex flex-col items-start gap-3 sm:items-end">
              <div className="flex gap-1 rounded-full bg-white/15 p-1 backdrop-blur">
                {PRESETS.map((preset) => {
                  const active = dateTo === isoDaysAgo(0) && dateFrom === isoDaysAgo(preset.days);
                  return (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => {
                        setDateFrom(isoDaysAgo(preset.days));
                        setDateTo(isoDaysAgo(0));
                      }}
                      className={cn(
                        "rounded-full px-4 py-1.5 text-button transition-colors duration-micro",
                        active
                          ? "bg-white text-primary shadow-level-1"
                          : "text-white/90 hover:bg-white/15",
                      )}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>
              <div className="flex items-center gap-2 rounded-md bg-white p-1.5 shadow-level-2">
                <CalendarRange className="ml-1.5 h-4 w-4 text-text-secondary" />
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="h-9 w-auto border-0 shadow-none"
                  aria-label="From date"
                />
                <span className="text-text-secondary">to</span>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="h-9 w-auto border-0 shadow-none"
                  aria-label="To date"
                />
              </div>
            </div>
          </div>
        </div>
      </FadeIn>

      {isLoading && <DashboardSkeleton />}

      {isError && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <AlertTriangle className="h-6 w-6 text-danger" />
            <p className="text-body text-text-secondary">
              Unable to load analytics for this range.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && data && (
        <AnalyticsCharts data={data} isPlatform={isPlatform} isDoctor={isDoctor} />
      )}
    </div>
  );
}
