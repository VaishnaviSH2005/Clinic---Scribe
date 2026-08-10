"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { AlertTriangle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalytics } from "@/features/analytics/hooks/use-analytics";

// recharts is a large dependency used only on this page — dynamically
// imported so it never ships in the shared bundle for every other route.
const AnalyticsCharts = dynamic(
  () => import("@/features/analytics/components/analytics-charts").then((m) => m.AnalyticsCharts),
  { ssr: false, loading: () => <Skeleton className="h-72 w-full" /> },
);

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function AnalyticsPage() {
  const [dateFrom, setDateFrom] = useState(isoDaysAgo(29));
  const [dateTo, setDateTo] = useState(isoDaysAgo(0));
  const { data, isLoading, isError } = useAnalytics({ dateFrom, dateTo });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-h2 text-text-primary">Analytics</h1>
          <p className="mt-1 text-body text-text-secondary">
            Operational insights and consultation trends.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-auto"
          />
          <span className="text-text-secondary">to</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-auto"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      )}

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
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="py-5">
                <p className="text-caption font-medium uppercase text-text-secondary">
                  Reports generated
                </p>
                <p className="mt-2 text-h2 text-text-primary">{data.reports_generated}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="py-5">
                <p className="text-caption font-medium uppercase text-text-secondary">
                  Missed appointment rate
                </p>
                <p className="mt-2 text-h2 text-text-primary">{data.missed_appointment_rate}%</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="py-5">
                <p className="text-caption font-medium uppercase text-text-secondary">
                  AI pipeline success
                </p>
                <p className="mt-2 text-h2 text-text-primary">
                  {data.ai_processing_outcomes.ai_pipeline_completed ?? 0}
                </p>
                <p className="text-caption text-text-secondary">
                  {data.ai_processing_outcomes.ai_stage_failed ?? 0} stage failures
                </p>
              </CardContent>
            </Card>
          </div>

          <AnalyticsCharts
            consultationsPerDay={data.consultations_per_day}
            newPatientsPerDay={data.new_patients_per_day}
          />

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Consultations by status</CardTitle>
              </CardHeader>
              <CardContent>
                <NamedCountTable
                  data={Object.entries(data.consultations_by_status).map(([name, count]) => ({
                    name,
                    count,
                  }))}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Appointments by status</CardTitle>
              </CardHeader>
              <CardContent>
                <NamedCountTable
                  data={Object.entries(data.appointments_by_status).map(([name, count]) => ({
                    name,
                    count,
                  }))}
                />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Consultations by doctor</CardTitle>
              </CardHeader>
              <CardContent>
                <NamedCountTable data={data.consultations_by_doctor} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Consultations by department</CardTitle>
              </CardHeader>
              <CardContent>
                <NamedCountTable data={data.consultations_by_department} />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function NamedCountTable({ data }: { data: { name: string; count: number }[] }) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-body text-text-secondary">No data for this range.</p>
    );
  }
  return (
    <table className="w-full text-left">
      <tbody>
        {data.map((row) => (
          <tr key={row.name} className="border-t border-border first:border-t-0">
            <td className="py-2 text-body capitalize text-text-primary">
              {row.name.replace(/_/g, " ")}
            </td>
            <td className="py-2 text-right text-body font-medium text-text-primary">{row.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
