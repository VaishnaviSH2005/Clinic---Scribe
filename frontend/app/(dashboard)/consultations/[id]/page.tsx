import { ConsultationWorkspaceView } from "@/features/consultation/components/consultation-workspace-view";

interface ConsultationWorkspacePageProps {
  params: Promise<{ id: string }>;
}

// The workspace escapes the dashboard shell's default page padding/max-width
// (Ch9.1 — "premium, distraction-free" full-bleed workspace, unlike the
// standard CRUD pages) by cancelling out the parent <main> padding.
export default async function ConsultationWorkspacePage({
  params,
}: ConsultationWorkspacePageProps) {
  const { id } = await params;
  return (
    <div className="-mx-8 -my-6 h-[calc(100vh-72px)] max-w-none">
      <ConsultationWorkspaceView consultationId={id} />
    </div>
  );
}
