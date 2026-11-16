"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, FileText } from "lucide-react";

import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { HospitalSelector, useHospitalChoice } from "@/features/hospital-scope/hospital-scope";
import { ROUTES } from "@/constants/routes";
import { useReports } from "@/features/reports/hooks/use-reports";
import { formatDateTime } from "@/lib/date";
import type { Report } from "@/types/report";

const PAGE_SIZE = 10;

export default function ReportsPage() {
  const router = useRouter();
  const { user } = useAuth();
  // Super Admin has no hospital of their own: they browse ONE chosen hospital's reports (read-only).
  const isSuperAdmin = user?.role === "super_admin";
  const { hospitalId, choose } = useHospitalChoice(isSuperAdmin);
  const [page, setPage] = useState(1);
  const needsHospital = isSuperAdmin && !hospitalId;
  const { data, isLoading, isError } = useReports({
    page,
    pageSize: PAGE_SIZE,
    hospitalId: isSuperAdmin ? hospitalId : undefined,
    enabled: !!user && !needsHospital,
  });
  const reportHref = (id: string) =>
    isSuperAdmin ? `${ROUTES.reports}/${id}?hospital=${hospitalId}` : `${ROUTES.reports}/${id}`;

  const columns: DataTableColumn<Report>[] = [
    {
      header: "Report",
      accessor: (r) => (
        <button
          onClick={() => router.push(reportHref(r.id))}
          className="flex items-center gap-2 text-left text-text-primary hover:underline"
        >
          <FileText className="h-4 w-4 text-text-secondary" />
          {r.report_type.replace(/_/g, " ")}
        </button>
      ),
    },
    { header: "Version", accessor: (r) => `v${r.current_version}` },
    { header: "Generated", accessor: (r) => formatDateTime(r.created_at) },
    {
      header: "Follow-up",
      accessor: (r) => (r.follow_up_date ? formatDateTime(r.follow_up_date) : "—"),
    },
    {
      header: "Actions",
      accessor: (r) => (
        <Button variant="ghost" size="sm" onClick={() => router.push(reportHref(r.id))}>
          View
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Reports</h1>
        <p className="mt-1 text-body text-text-secondary">
          Generated consultation and clinical reports.
        </p>
      </div>

      {isSuperAdmin && (
        <HospitalSelector
          value={hospitalId}
          onChange={(id) => {
            choose(id);
            setPage(1);
          }}
        />
      )}

      {needsHospital ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
            <Building2 className="h-8 w-8 text-text-secondary" />
            <p className="text-body-lg font-medium text-text-primary">Choose a hospital</p>
            <p className="text-body text-text-secondary">
              Reports are private to each hospital. Select one above to view its reports.
            </p>
          </CardContent>
        </Card>
      ) : (
        <DataTable
          columns={columns}
          data={data?.data ?? []}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          emptyState={{
            title: "No reports yet.",
            description: "Reports are generated automatically when a consultation is approved.",
          }}
          page={page}
          pageSize={PAGE_SIZE}
          total={data?.pagination.total ?? 0}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
