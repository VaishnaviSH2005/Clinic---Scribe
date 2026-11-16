"use client";

import { useState } from "react";

import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import type { AuditLog } from "@/types/audit-log";

import { useAuditLogs } from "../hooks/use-audit-logs";

const PAGE_SIZE = 20;

// Shared by the Super Admin "Audit Logs" page (platform-wide) and the Hospital
// Admin Settings tab (own hospital only, PRD Ch13.8) — the backend decides what
// each role is allowed to see.
export function AuditLogTable({ showHospital }: { showHospital: boolean }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useAuditLogs(page, PAGE_SIZE);

  const columns: DataTableColumn<AuditLog>[] = [
    {
      header: "Action",
      accessor: (l) => <span className="capitalize">{l.action.replace(/_/g, " ")}</span>,
    },
    { header: "Entity", accessor: (l) => l.entity_type ?? "—" },
    {
      header: "User",
      accessor: (l) =>
        l.user_name ? (
          <div>
            <p className="text-body font-medium text-text-primary">{l.user_name}</p>
            <p className="text-caption text-text-secondary">{l.user_email}</p>
          </div>
        ) : (
          "System"
        ),
    },
    ...(showHospital
      ? [{ header: "Hospital", accessor: (l: AuditLog) => l.hospital_name ?? "Platform" }]
      : []),
    { header: "When", accessor: (l) => new Date(l.created_at).toLocaleString() },
  ];

  return (
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
  );
}
