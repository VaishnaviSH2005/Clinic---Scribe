import { PatientDetailView } from "@/features/patients/components/patient-detail-view";

interface PatientDetailPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ hospital?: string }>;
}

export default async function PatientDetailPage({ params, searchParams }: PatientDetailPageProps) {
  const { id } = await params;
  const { hospital } = await searchParams;
  return <PatientDetailView patientId={id} hospitalId={hospital} />;
}
