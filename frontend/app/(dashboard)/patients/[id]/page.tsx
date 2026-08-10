import { PatientDetailView } from "@/features/patients/components/patient-detail-view";

interface PatientDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function PatientDetailPage({ params }: PatientDetailPageProps) {
  const { id } = await params;
  return <PatientDetailView patientId={id} />;
}
