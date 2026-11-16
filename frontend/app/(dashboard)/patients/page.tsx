"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { PatientRegistrationDialog } from "@/features/patients/components/patient-registration-dialog";
import { usePatientMutations, usePatients } from "@/features/patients/hooks/use-patients";
import { HospitalSelector, useHospitalChoice } from "@/features/hospital-scope/hospital-scope";
import { formatDate } from "@/lib/date";
import type { Patient } from "@/types/patient";

const PAGE_SIZE = 10;

export default function PatientsPage() {
  const router = useRouter();
  const { user } = useAuth();
  // Super Admin has no hospital of their own: they browse ONE chosen
  // hospital's patients, read-only (PRD Ch6.15 / Ch6.3).
  const isSuperAdmin = user?.role === "super_admin";
  const { hospitalId, choose } = useHospitalChoice(isSuperAdmin);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<Patient | null>(null);

  const chooseHospital = (id: string) => {
    choose(id);
    setPage(1);
  };

  const needsHospital = isSuperAdmin && !hospitalId;
  const { data, isLoading, isError } = usePatients({
    page,
    pageSize: PAGE_SIZE,
    search: search || undefined,
    includeArchived,
    hospitalId: isSuperAdmin ? hospitalId : undefined,
    enabled: !!user && !needsHospital,
  });
  const patientHref = (id: string) =>
    isSuperAdmin ? `/patients/${id}?hospital=${hospitalId}` : `/patients/${id}`;
  const { archive, restore } = usePatientMutations();

  const columns: DataTableColumn<Patient>[] = [
    {
      header: "Patient",
      accessor: (p) => (
        <button
          className="text-left font-medium text-primary hover:underline"
          onClick={() => router.push(patientHref(p.id))}
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
          <Button variant="ghost" size="sm" onClick={() => router.push(patientHref(p.id))}>
            View
          </Button>
          {!isSuperAdmin &&
            (p.status === "active" ? (
              <Button variant="ghost" size="sm" onClick={() => setArchiveTarget(p)}>
                Archive
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => restore.mutate(p.id)}>
                Restore
              </Button>
            ))}
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
            {isSuperAdmin
              ? "View-only access to the patient records of one hospital at a time."
              : "Register, search, and manage patient records."}
          </p>
        </div>
        {!isSuperAdmin && (
          <Button onClick={() => setRegisterOpen(true)}>
            <Plus className="h-4 w-4" /> Register patient
          </Button>
        )}
      </div>

      {isSuperAdmin && <HospitalSelector value={hospitalId} onChange={chooseHospital} />}

      {needsHospital ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
            <Building2 className="h-8 w-8 text-text-secondary" />
            <p className="text-body-lg font-medium text-text-primary">Choose a hospital</p>
            <p className="text-body text-text-secondary">
              Patient records are private to each hospital. Select one above to view its patients.
            </p>
          </CardContent>
        </Card>
      ) : (
        <DataTable
          columns={columns}
          data={data?.data ?? []}
          rowKey={(p) => p.id}
          isLoading={isLoading}
          isError={isError}
          emptyState={{
            title: "No patients found.",
            description: isSuperAdmin
              ? "This hospital has no registered patients."
              : "Register the first patient to get started.",
            action: isSuperAdmin ? undefined : (
              <Button onClick={() => setRegisterOpen(true)}>Register patient</Button>
            ),
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
      )}

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
