import { Badge } from "@/components/ui/badge";

const VARIANTS: Record<string, "success" | "warning" | "danger" | "outline" | "default"> = {
  // Generic active/inactive (hospitals, departments, users)
  active: "success",
  inactive: "outline",
  suspended: "danger",
  trial: "warning",
  expired: "danger",
  cancelled: "outline",
  archived: "outline",
  // Appointments (PRD Ch8.10)
  upcoming: "outline",
  checked_in: "warning",
  completed: "success",
  missed: "danger",
  // Consultations (PRD Ch9.3)
  draft: "outline",
  in_progress: "warning",
  ai_processing: "warning",
  pending_review: "warning",
  approved: "success",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant={VARIANTS[status] ?? "outline"} className="capitalize">
      {status.replace("_", " ")}
    </Badge>
  );
}
