import { ReportDetailView } from "@/features/reports/components/report-detail-view";

interface ReportDetailPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ hospital?: string }>;
}

export default async function ReportDetailPage({ params, searchParams }: ReportDetailPageProps) {
  const { id } = await params;
  const { hospital } = await searchParams;
  return <ReportDetailView id={id} hospitalId={hospital} />;
}
