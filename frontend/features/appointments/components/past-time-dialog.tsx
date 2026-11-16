"use client";

import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";

// Shown when the server reports the chosen time has already passed. The user
// either picks another time or explicitly books it anyway (e.g. back-filling a
// visit that already happened) — never a silent block, never a silent accept.
export function PastTimeDialog({
  open,
  onChooseAnother,
  onBookAnyway,
  loading,
}: {
  open: boolean;
  onChooseAnother: () => void;
  onBookAnyway: () => void;
  loading?: boolean;
}) {
  return (
    <ConfirmDialog
      open={open}
      onOpenChange={(next) => !next && onChooseAnother()}
      title="That time has already passed"
      description="The date and time you picked is in the past. Choose another time, or book it anyway if you are recording a visit that already happened."
      confirmLabel="Book anyway"
      cancelLabel="Choose another time"
      loading={loading}
      onConfirm={onBookAnyway}
    />
  );
}
