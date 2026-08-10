"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Department } from "@/types/department";

import { useDepartmentMutations, useDepartments } from "../hooks/use-departments";
import { DepartmentFormDialog } from "./department-form-dialog";

const PAGE_SIZE = 10;

export function DepartmentsTab() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [statusTarget, setStatusTarget] = useState<Department | null>(null);

  const { data, isLoading, isError } = useDepartments(page, PAGE_SIZE);
  const { create, update, updateStatus } = useDepartmentMutations();

  const columns: DataTableColumn<Department>[] = [
    { header: "Name", accessor: (d) => d.name },
    { header: "Status", accessor: (d) => <StatusBadge status={d.status} /> },
    {
      header: "Actions",
      accessor: (d) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setEditing(d);
              setDialogOpen(true);
            }}
          >
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setStatusTarget(d)}>
            {d.status === "active" ? "Disable" : "Enable"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Departments</CardTitle>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Add department
        </Button>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={data?.data ?? []}
          rowKey={(d) => d.id}
          isLoading={isLoading}
          isError={isError}
          emptyState={{
            title: "No departments found.",
            description: "Add the first department to get started.",
          }}
          page={page}
          pageSize={PAGE_SIZE}
          total={data?.pagination.total ?? 0}
          onPageChange={setPage}
        />
      </CardContent>

      <DepartmentFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        department={editing}
        loading={create.isPending || update.isPending}
        onSubmit={(values) => {
          if (editing) {
            update.mutate(
              { id: editing.id, payload: values },
              { onSuccess: () => setDialogOpen(false) },
            );
          } else {
            create.mutate(values, { onSuccess: () => setDialogOpen(false) });
          }
        }}
      />

      <ConfirmDialog
        open={!!statusTarget}
        onOpenChange={(open) => !open && setStatusTarget(null)}
        title={statusTarget?.status === "active" ? "Disable department?" : "Enable department?"}
        description={
          statusTarget?.status === "active"
            ? `"${statusTarget?.name}" will no longer be available for new assignments.`
            : `"${statusTarget?.name}" will become available again.`
        }
        confirmLabel={statusTarget?.status === "active" ? "Disable" : "Enable"}
        danger={statusTarget?.status === "active"}
        loading={updateStatus.isPending}
        onConfirm={() => {
          if (!statusTarget) return;
          updateStatus.mutate(
            {
              id: statusTarget.id,
              status: statusTarget.status === "active" ? "inactive" : "active",
            },
            { onSuccess: () => setStatusTarget(null) },
          );
        }}
      />
    </Card>
  );
}
