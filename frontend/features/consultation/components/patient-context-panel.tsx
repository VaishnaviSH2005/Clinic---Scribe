import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/badges/status-badge";
import { formatDate } from "@/lib/date";
import type { ConsultationPatientContext } from "@/types/consultation";

function AlertSection({
  title,
  items,
  variant,
}: {
  title: string;
  items: string[];
  variant?: "danger";
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="mb-1.5 text-caption font-medium uppercase text-text-secondary">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <Badge key={item} variant={variant ?? "outline"}>
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

// Left Panel — Patient Context (PRD Ch9.5). Always visible during the
// consultation; critical alerts appear first.
export function PatientContextPanel({ patient }: { patient: ConsultationPatientContext }) {
  const { medical_alerts: alerts } = patient;
  const hasAlerts = alerts.known_allergies.length > 0 || alerts.chronic_diseases.length > 0;

  return (
    <aside className="flex w-[240px] shrink-0 flex-col gap-6 overflow-y-auto border-r border-border bg-surface p-6 lg:w-[300px]">
      <div>
        <h2 className="text-h5 text-text-primary">{patient.full_name}</h2>
        <p className="text-body text-text-secondary">
          {patient.uhid} · {patient.age} yrs · {patient.gender}
        </p>
        {patient.blood_group && (
          <p className="text-body text-text-secondary">Blood group: {patient.blood_group}</p>
        )}
      </div>

      {hasAlerts && (
        <div className="flex items-start gap-2 rounded-md border border-danger/30 bg-danger/5 p-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
          <div className="flex flex-col gap-3">
            <AlertSection title="Allergies" items={alerts.known_allergies} variant="danger" />
            <AlertSection title="Chronic conditions" items={alerts.chronic_diseases} />
          </div>
        </div>
      )}

      <AlertSection title="Current medications" items={alerts.current_medications} />

      <div>
        <p className="mb-2 text-caption font-medium uppercase text-text-secondary">
          Previous consultations
        </p>
        {patient.previous_consultations.length === 0 ? (
          <p className="text-body text-text-secondary">No previous consultations.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {patient.previous_consultations.map((c) => (
              <li key={c.id} className="flex flex-col gap-1 rounded-md border border-border p-3">
                <div className="flex items-center justify-between">
                  <span className="text-caption text-text-secondary">
                    {c.started_at ? formatDate(c.started_at) : "—"}
                  </span>
                  <StatusBadge status={c.status} />
                </div>
                {c.chief_complaint && (
                  <p className="text-body text-text-primary">{c.chief_complaint}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
