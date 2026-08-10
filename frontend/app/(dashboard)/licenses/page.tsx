"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { useHospitals } from "@/features/settings/hooks/use-hospitals";
import { LicenseFormDialog } from "@/features/licenses/components/license-form-dialog";
import { useLicenseMutations, useLicenses } from "@/features/licenses/hooks/use-licenses";
import type { Subscription } from "@/types/subscription";

const PAGE_SIZE = 10;

export default function LicensesPage() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data, isLoading, isError } = useLicenses(page, PAGE_SIZE);
  const { data: hospitalsData } = useHospitals(1, 100);
  const { create, updateStatus } = useLicenseMutations();

  const hospitalName = (hospitalId: string) =>
    hospitalsData?.data.find((h) => h.id === hospitalId)?.name ?? hospitalId;

  const columns: DataTableColumn<Subscription>[] = [
    { header: "Hospital", accessor: (s) => hospitalName(s.hospital_id) },
    { header: "Plan", accessor: (s) => s.plan_name },
    { header: "Status", accessor: (s) => <StatusBadge status={s.status} /> },
    { header: "Starts", accessor: (s) => s.starts_at },
    { header: "Expires", accessor: (s) => s.expires_at },
    {
      header: "Actions",
      accessor: (s) => (
        <div className="flex gap-2">
          {s.status !== "cancelled" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => updateStatus.mutate({ id: s.id, status: "cancelled" })}
            >
              Cancel
            </Button>
          )}
          {s.status !== "active" && s.status !== "cancelled" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => updateStatus.mutate({ id: s.id, status: "active" })}
            >
              Activate
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Licenses</h1>
        <p className="mt-1 text-body text-text-secondary">
          Manage hospital subscriptions and license status.
        </p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Licenses</CardTitle>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4" /> Add license
          </Button>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data?.data ?? []}
            rowKey={(s) => s.id}
            isLoading={isLoading}
            isError={isError}
            emptyState={{
              title: "No licenses found.",
              description: "Add a license to get started.",
            }}
            page={page}
            pageSize={PAGE_SIZE}
            total={data?.pagination.total ?? 0}
            onPageChange={setPage}
          />
        </CardContent>
      </Card>

      <LicenseFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        hospitals={hospitalsData?.data ?? []}
        loading={create.isPending}
        onSubmit={(values) => create.mutate(values, { onSuccess: () => setDialogOpen(false) })}
      />
    </div>
  );
}
