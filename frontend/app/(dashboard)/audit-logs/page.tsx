"use client";

import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { useAuditLogs } from "@/features/audit-logs/hooks/use-audit-logs";
import type { AuditLog } from "@/types/audit-log";

const PAGE_SIZE = 20;

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useAuditLogs(page, PAGE_SIZE);

  const columns: DataTableColumn<AuditLog>[] = [
    { header: "Action", accessor: (l) => l.action.replace(/_/g, " ") },
    { header: "Entity", accessor: (l) => l.entity_type ?? "—" },
    { header: "User ID", accessor: (l) => l.user_id ?? "—" },
    { header: "Hospital ID", accessor: (l) => l.hospital_id ?? "—" },
    { header: "When", accessor: (l) => new Date(l.created_at).toLocaleString() },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Audit Logs</h1>
        <p className="mt-1 text-body text-text-secondary">
          Platform-wide record of authentication and administrative events.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data?.data ?? []}
            rowKey={(l) => l.id}
            isLoading={isLoading}
            isError={isError}
            emptyState={{ title: "No audit events found." }}
            page={page}
            pageSize={PAGE_SIZE}
            total={data?.pagination.total ?? 0}
            onPageChange={setPage}
          />
        </CardContent>
      </Card>
    </div>
  );
}
