"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/badges/status-badge";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import type { Hospital } from "@/types/hospital";

import { useHospitalMutations, useHospitals } from "../hooks/use-hospitals";
import { hospitalService } from "../services/hospital.service";
import { HospitalFormDialog } from "./hospital-form-dialog";

const PAGE_SIZE = 10;

export function SuperAdminHospitals() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Hospital | null>(null);
  const { data, isLoading, isError } = useHospitals(page, PAGE_SIZE);
  const { create, update, updateStatus, uploadLogo } = useHospitalMutations();

  const columns: DataTableColumn<Hospital>[] = [
    { header: "Name", accessor: (h) => h.name },
    { header: "Registration #", accessor: (h) => h.registration_number },
    { header: "Email", accessor: (h) => h.email },
    { header: "Status", accessor: (h) => <StatusBadge status={h.status} /> },
    {
      header: "Actions",
      accessor: (h) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setEditing(h);
              setDialogOpen(true);
            }}
          >
            Edit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              updateStatus.mutate({
                id: h.id,
                status: h.status === "active" ? "inactive" : "active",
              })
            }
          >
            {h.status === "active" ? "Deactivate" : "Activate"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Hospitals</CardTitle>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Add hospital
        </Button>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={data?.data ?? []}
          rowKey={(h) => h.id}
          isLoading={isLoading}
          isError={isError}
          emptyState={{
            title: "No hospitals found.",
            description: "Add the first hospital to get started.",
          }}
          page={page}
          pageSize={PAGE_SIZE}
          total={data?.pagination.total ?? 0}
          onPageChange={setPage}
        />
      </CardContent>
      <HospitalFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        hospital={editing}
        loading={create.isPending || update.isPending}
        logoUploading={uploadLogo.isPending}
        onUploadLogo={(file) => editing && uploadLogo.mutate({ id: editing.id, file })}
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
    </Card>
  );
}

function HospitalAdminHospital({ hospitalId }: { hospitalId: string }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: hospital, isLoading } = useQuery({
    queryKey: ["hospitals", "own", hospitalId],
    queryFn: () => hospitalService.get(hospitalId),
  });
  const { update, uploadLogo } = useHospitalMutations();

  if (isLoading || !hospital) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hospital details</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-body text-text-secondary">Loading hospital details…</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Hospital details</CardTitle>
        <Button onClick={() => setDialogOpen(true)}>Edit</Button>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4 text-body">
        <div>
          <p className="text-caption text-text-secondary">Name</p>
          <p className="text-text-primary">{hospital.name}</p>
        </div>
        <div>
          <p className="text-caption text-text-secondary">Registration number</p>
          <p className="text-text-primary">{hospital.registration_number}</p>
        </div>
        <div>
          <p className="text-caption text-text-secondary">Email</p>
          <p className="text-text-primary">{hospital.email}</p>
        </div>
        <div>
          <p className="text-caption text-text-secondary">Phone</p>
          <p className="text-text-primary">{hospital.phone}</p>
        </div>
        <div>
          <p className="text-caption text-text-secondary">Status</p>
          <StatusBadge status={hospital.status} />
        </div>
      </CardContent>
      <HospitalFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        hospital={hospital}
        loading={update.isPending}
        logoUploading={uploadLogo.isPending}
        onUploadLogo={(file) => uploadLogo.mutate({ id: hospital.id, file })}
        onSubmit={(values) =>
          update.mutate(
            { id: hospital.id, payload: values },
            { onSuccess: () => setDialogOpen(false) },
          )
        }
      />
    </Card>
  );
}

export function HospitalsTab() {
  const { user } = useAuth();
  if (!user) return null;
  if (user.role === "super_admin") return <SuperAdminHospitals />;
  if (user.hospitalId) return <HospitalAdminHospital hospitalId={user.hospitalId} />;
  return null;
}
