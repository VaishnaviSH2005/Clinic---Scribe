"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import type { DataTableColumn } from "@/components/tables/data-table";
import { DataTable } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StartConsultationDialog } from "@/features/consultation/components/start-consultation-dialog";
import { useConsultations } from "@/features/consultation/hooks/use-consultations";
import { formatDateTime } from "@/lib/date";
import type { Consultation, ConsultationScope } from "@/types/consultation";

const PAGE_SIZE = 10;

const SCOPE_LABELS: Record<ConsultationScope, string> = {
  active: "Active",
  drafts: "Drafts",
  previous: "Previous",
};

const SCOPE_EMPTY: Record<ConsultationScope, string> = {
  active: "No active consultations. Start a new consultation to begin.",
  drafts: "No draft consultations.",
  previous: "No completed consultations yet.",
};

export default function ConsultationsPage() {
  const router = useRouter();
  const [scope, setScope] = useState<ConsultationScope>("active");
  const [page, setPage] = useState(1);
  const [startOpen, setStartOpen] = useState(false);

  const { data, isLoading, isError } = useConsultations(scope, page, PAGE_SIZE);

  const columns: DataTableColumn<Consultation>[] = [
    {
      header: "Started",
      accessor: (c) => (c.started_at ? formatDateTime(c.started_at) : "—"),
    },
    { header: "Chief complaint", accessor: (c) => c.chief_complaint || "—" },
    { header: "Status", accessor: (c) => <StatusBadge status={c.status} /> },
    {
      header: "Actions",
      accessor: (c) => (
        <Button variant="ghost" size="sm" onClick={() => router.push(`/consultations/${c.id}`)}>
          Open
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h2 text-text-primary">Consultations</h1>
          <p className="mt-1 text-body text-text-secondary">AI-assisted consultation workspace.</p>
        </div>
        <Button onClick={() => setStartOpen(true)}>
          <Plus className="h-4 w-4" /> Start consultation
        </Button>
      </div>

      <Tabs
        value={scope}
        onValueChange={(value) => {
          setScope(value as ConsultationScope);
          setPage(1);
        }}
      >
        <TabsList>
          {(Object.keys(SCOPE_LABELS) as ConsultationScope[]).map((key) => (
            <TabsTrigger key={key} value={key}>
              {SCOPE_LABELS[key]}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey={(c) => c.id}
        isLoading={isLoading}
        isError={isError}
        emptyState={{
          title: SCOPE_EMPTY[scope],
          action:
            scope === "active" ? (
              <Button onClick={() => setStartOpen(true)}>Start consultation</Button>
            ) : undefined,
        }}
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.pagination.total ?? 0}
        onPageChange={setPage}
      />

      <StartConsultationDialog open={startOpen} onOpenChange={setStartOpen} />
    </div>
  );
}
