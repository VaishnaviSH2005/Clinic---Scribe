"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { AppointmentFormDialog } from "@/features/appointments/components/appointment-form-dialog";
import { RescheduleDialog } from "@/features/appointments/components/reschedule-dialog";
import {
  useAppointmentMutations,
  useAppointments,
} from "@/features/appointments/hooks/use-appointments";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { useDepartments } from "@/features/settings/hooks/use-departments";
import { useDoctors } from "@/features/settings/hooks/use-staff";
import { formatDateTime } from "@/lib/date";
import type { Appointment, AppointmentStatus } from "@/types/appointment";

const PAGE_SIZE = 10;

function todayRange() {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return { dateFrom: start.toISOString(), dateTo: end.toISOString() };
}

export default function AppointmentsPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [dateFilter, setDateFilter] = useState<"today" | "all">("today");
  const [doctorId, setDoctorId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [status, setStatus] = useState<AppointmentStatus | "">("");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [rescheduleTarget, setRescheduleTarget] = useState<Appointment | null>(null);
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);

  const { dateFrom, dateTo } = useMemo(todayRange, []);
  const { data: departmentsData } = useDepartments(1, 100);
  const { data: doctorsData } = useDoctors({ page: 1, pageSize: 100 });
  const departments = useMemo(() => departmentsData?.data ?? [], [departmentsData]);
  const doctors = useMemo(() => doctorsData?.data ?? [], [doctorsData]);
  const doctorNames = useMemo(() => new Map(doctors.map((d) => [d.id, d.full_name])), [doctors]);
  const departmentNames = useMemo(
    () => new Map(departments.map((d) => [d.id, d.name])),
    [departments],
  );

  const { data, isLoading, isError } = useAppointments({
    page,
    pageSize: PAGE_SIZE,
    dateFrom: dateFilter === "today" ? dateFrom : undefined,
    dateTo: dateFilter === "today" ? dateTo : undefined,
    doctorId: doctorId || undefined,
    departmentId: departmentId || undefined,
    status: status || undefined,
  });
  const { checkIn, cancel } = useAppointmentMutations();

  const columns: DataTableColumn<Appointment>[] = [
    { header: "Date & time", accessor: (a) => formatDateTime(a.scheduled_at) },
    { header: "Doctor", accessor: (a) => doctorNames.get(a.doctor_id) ?? "—" },
    { header: "Department", accessor: (a) => departmentNames.get(a.department_id) ?? "—" },
    { header: "Status", accessor: (a) => <StatusBadge status={a.status} /> },
    {
      header: "Actions",
      accessor: (a) => (
        <div className="flex gap-2">
          {a.status === "upcoming" && user?.role === "receptionist" && (
            <Button variant="ghost" size="sm" onClick={() => checkIn.mutate(a.id)}>
              Check in
            </Button>
          )}
          {(a.status === "upcoming" || a.status === "checked_in") && (
            <Button variant="ghost" size="sm" onClick={() => setRescheduleTarget(a)}>
              Reschedule
            </Button>
          )}
          {a.status !== "completed" && a.status !== "cancelled" && (
            <Button variant="ghost" size="sm" onClick={() => setCancelTarget(a)}>
              Cancel
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
          <h1 className="text-h2 text-text-primary">Appointments</h1>
          <p className="mt-1 text-body text-text-secondary">
            Schedule, check in, and manage appointments.
          </p>
        </div>
        <Button onClick={() => setScheduleOpen(true)}>
          <Plus className="h-4 w-4" /> Schedule appointment
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey={(a) => a.id}
        isLoading={isLoading}
        isError={isError}
        emptyState={{
          title: "No appointments found.",
          description: "Schedule the first appointment to get started.",
          action: <Button onClick={() => setScheduleOpen(true)}>Schedule appointment</Button>,
        }}
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.pagination.total ?? 0}
        onPageChange={setPage}
        toolbar={
          <div className="flex flex-wrap items-center gap-2">
            <Select
              value={dateFilter}
              onChange={(e) => {
                setDateFilter(e.target.value as "today" | "all");
                setPage(1);
              }}
              className="w-auto"
            >
              <option value="today">Today</option>
              <option value="all">All dates</option>
            </Select>
            <Select
              value={departmentId}
              onChange={(e) => {
                setDepartmentId(e.target.value);
                setPage(1);
              }}
              className="w-auto"
            >
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
            <Select
              value={doctorId}
              onChange={(e) => {
                setDoctorId(e.target.value);
                setPage(1);
              }}
              className="w-auto"
            >
              <option value="">All doctors</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name}
                </option>
              ))}
            </Select>
            <Select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value as AppointmentStatus | "");
                setPage(1);
              }}
              className="w-auto"
            >
              <option value="">All statuses</option>
              <option value="upcoming">Upcoming</option>
              <option value="checked_in">Checked in</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="missed">Missed</option>
            </Select>
          </div>
        }
      />

      <AppointmentFormDialog open={scheduleOpen} onOpenChange={setScheduleOpen} />
      <RescheduleDialog
        open={!!rescheduleTarget}
        onOpenChange={(open) => !open && setRescheduleTarget(null)}
        appointment={rescheduleTarget}
      />
      <ConfirmDialog
        open={!!cancelTarget}
        onOpenChange={(open) => !open && setCancelTarget(null)}
        title="Cancel appointment?"
        description="This appointment will be marked as cancelled."
        confirmLabel="Cancel appointment"
        danger
        loading={cancel.isPending}
        onConfirm={() => {
          if (!cancelTarget) return;
          cancel.mutate(cancelTarget.id, { onSuccess: () => setCancelTarget(null) });
        }}
      />
    </div>
  );
}
