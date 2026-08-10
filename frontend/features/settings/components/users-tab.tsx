"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { StaffUser } from "@/types/user";

import { useDepartments } from "../hooks/use-departments";
import { useDoctors, useReceptionists, useStaffMutations } from "../hooks/use-staff";
import { DoctorFormDialog } from "./doctor-form-dialog";
import { ReceptionistFormDialog } from "./receptionist-form-dialog";

const PAGE_SIZE = 10;

function DoctorsSection() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<StaffUser | null>(null);
  const [statusTarget, setStatusTarget] = useState<StaffUser | null>(null);

  const { data: departmentsData } = useDepartments(1, 100);
  const departments = departmentsData?.data ?? [];

  const { data, isLoading, isError } = useDoctors({
    page,
    pageSize: PAGE_SIZE,
    search: search || undefined,
  });
  const { createDoctor, updateDoctor, updateDoctorStatus } = useStaffMutations();

  const columns: DataTableColumn<StaffUser>[] = [
    { header: "Name", accessor: (d) => d.full_name },
    { header: "Email", accessor: (d) => d.email },
    { header: "Specialization", accessor: (d) => d.specialization ?? "—" },
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
            {d.status === "active" ? "Deactivate" : "Activate"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <div className="mb-4 flex justify-end">
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Add doctor
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey={(d) => d.id}
        isLoading={isLoading}
        isError={isError}
        emptyState={{
          title: "No doctors found.",
          description: "Add the first doctor to get started.",
        }}
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.pagination.total ?? 0}
        onPageChange={setPage}
        search={search}
        onSearchChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        searchPlaceholder="Search doctors…"
      />

      <DoctorFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        doctor={editing}
        departments={departments}
        loading={createDoctor.isPending || updateDoctor.isPending}
        onSubmit={(values) => {
          if (editing) {
            updateDoctor.mutate(
              { id: editing.id, payload: values },
              { onSuccess: () => setDialogOpen(false) },
            );
          } else {
            createDoctor.mutate(values, { onSuccess: () => setDialogOpen(false) });
          }
        }}
      />

      <ConfirmDialog
        open={!!statusTarget}
        onOpenChange={(open) => !open && setStatusTarget(null)}
        title={statusTarget?.status === "active" ? "Deactivate doctor?" : "Activate doctor?"}
        description={`"${statusTarget?.full_name}" will ${statusTarget?.status === "active" ? "lose" : "regain"} access to CliniScribe AI.`}
        confirmLabel={statusTarget?.status === "active" ? "Deactivate" : "Activate"}
        danger={statusTarget?.status === "active"}
        loading={updateDoctorStatus.isPending}
        onConfirm={() => {
          if (!statusTarget) return;
          updateDoctorStatus.mutate(
            {
              id: statusTarget.id,
              status: statusTarget.status === "active" ? "inactive" : "active",
            },
            { onSuccess: () => setStatusTarget(null) },
          );
        }}
      />
    </>
  );
}

function ReceptionistsSection() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<StaffUser | null>(null);
  const [statusTarget, setStatusTarget] = useState<StaffUser | null>(null);

  const { data, isLoading, isError } = useReceptionists({
    page,
    pageSize: PAGE_SIZE,
    search: search || undefined,
  });
  const { createReceptionist, updateReceptionist, updateReceptionistStatus } = useStaffMutations();

  const columns: DataTableColumn<StaffUser>[] = [
    { header: "Name", accessor: (r) => r.full_name },
    { header: "Email", accessor: (r) => r.email },
    { header: "Phone", accessor: (r) => r.phone },
    { header: "Status", accessor: (r) => <StatusBadge status={r.status} /> },
    {
      header: "Actions",
      accessor: (r) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setEditing(r);
              setDialogOpen(true);
            }}
          >
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setStatusTarget(r)}>
            {r.status === "active" ? "Deactivate" : "Activate"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <div className="mb-4 flex justify-end">
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Add receptionist
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyState={{
          title: "No receptionists found.",
          description: "Add the first receptionist to get started.",
        }}
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.pagination.total ?? 0}
        onPageChange={setPage}
        search={search}
        onSearchChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        searchPlaceholder="Search receptionists…"
      />

      <ReceptionistFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        receptionist={editing}
        loading={createReceptionist.isPending || updateReceptionist.isPending}
        onSubmit={(values) => {
          if (editing) {
            updateReceptionist.mutate(
              { id: editing.id, payload: values },
              { onSuccess: () => setDialogOpen(false) },
            );
          } else {
            createReceptionist.mutate(values, { onSuccess: () => setDialogOpen(false) });
          }
        }}
      />

      <ConfirmDialog
        open={!!statusTarget}
        onOpenChange={(open) => !open && setStatusTarget(null)}
        title={
          statusTarget?.status === "active" ? "Deactivate receptionist?" : "Activate receptionist?"
        }
        description={`"${statusTarget?.full_name}" will ${statusTarget?.status === "active" ? "lose" : "regain"} access to CliniScribe AI.`}
        confirmLabel={statusTarget?.status === "active" ? "Deactivate" : "Activate"}
        danger={statusTarget?.status === "active"}
        loading={updateReceptionistStatus.isPending}
        onConfirm={() => {
          if (!statusTarget) return;
          updateReceptionistStatus.mutate(
            {
              id: statusTarget.id,
              status: statusTarget.status === "active" ? "inactive" : "active",
            },
            { onSuccess: () => setStatusTarget(null) },
          );
        }}
      />
    </>
  );
}

export function UsersTab() {
  const [section, setSection] = useState<"doctors" | "receptionists">("doctors");

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Users</CardTitle>
        <div className="bg-muted flex gap-1 rounded-md p-1">
          {(["doctors", "receptionists"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setSection(tab)}
              className={cn(
                "rounded-md px-3 py-1.5 text-body capitalize transition-colors",
                section === tab
                  ? "bg-surface text-text-primary shadow-level-1"
                  : "text-text-secondary",
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {section === "doctors" ? <DoctorsSection /> : <ReceptionistsSection />}
      </CardContent>
    </Card>
  );
}
