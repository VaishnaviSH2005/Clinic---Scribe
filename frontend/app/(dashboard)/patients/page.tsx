"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { PatientRegistrationDialog } from "@/features/patients/components/patient-registration-dialog";
import { usePatientMutations, usePatients } from "@/features/patients/hooks/use-patients";
import { formatDate } from "@/lib/date";
import type { Patient } from "@/types/patient";

const PAGE_SIZE = 10;

export default function PatientsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<Patient | null>(null);

  const { data, isLoading, isError } = usePatients({
    page,
    pageSize: PAGE_SIZE,
    search: search || undefined,
    includeArchived,
  });
  const { archive, restore } = usePatientMutations();

  const columns: DataTableColumn<Patient>[] = [
    {
      header: "Patient",
      accessor: (p) => (
        <button
          className="text-left font-medium text-primary hover:underline"
          onClick={() => router.push(`/patients/${p.id}`)}
        >
          {p.full_name}
        </button>
      ),
    },
    { header: "UHID", accessor: (p) => p.uhid },
    { header: "Age / Gender", accessor: (p) => `${p.age} / ${p.gender}` },
    { header: "Mobile", accessor: (p) => p.mobile_number },
    { header: "Registered", accessor: (p) => formatDate(p.created_at) },
    { header: "Status", accessor: (p) => <StatusBadge status={p.status} /> },
    {
      header: "Actions",
      accessor: (p) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => router.push(`/patients/${p.id}`)}>
            View
          </Button>
          {p.status === "active" ? (
            <Button variant="ghost" size="sm" onClick={() => setArchiveTarget(p)}>
              Archive
            </Button>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => restore.mutate(p.id)}>
              Restore
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h2 text-text-primary">Patients</h1>
          <p className="mt-1 text-body text-text-secondary">
            Register, search, and manage patient records.
          </p>
        </div>
        <Button onClick={() => setRegisterOpen(true)}>
          <Plus className="h-4 w-4" /> Register patient
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey={(p) => p.id}
        isLoading={isLoading}
        isError={isError}
        emptyState={{
          title: "No patients found.",
          description: "Register the first patient to get started.",
          action: <Button onClick={() => setRegisterOpen(true)}>Register patient</Button>,
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
        searchPlaceholder="Search by name, UHID, or mobile number…"
        toolbar={
          <label className="flex items-center gap-2 text-body text-text-secondary">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => {
                setIncludeArchived(e.target.checked);
                setPage(1);
              }}
              className="h-4 w-4 rounded border-border"
            />
            Show archived
          </label>
        }
      />

      <PatientRegistrationDialog
        open={registerOpen}
        onOpenChange={setRegisterOpen}
        onRegistered={(patientId) => router.push(`/patients/${patientId}`)}
      />

      <ConfirmDialog
        open={!!archiveTarget}
        onOpenChange={(open) => !open && setArchiveTarget(null)}
        title="Archive patient?"
        description={`"${archiveTarget?.full_name}" will be moved to archived records. This can be undone later.`}
        confirmLabel="Archive"
        danger
        loading={archive.isPending}
        onConfirm={() => {
          if (!archiveTarget) return;
          archive.mutate(archiveTarget.id, { onSuccess: () => setArchiveTarget(null) });
        }}
      />
    </div>
  );
}
