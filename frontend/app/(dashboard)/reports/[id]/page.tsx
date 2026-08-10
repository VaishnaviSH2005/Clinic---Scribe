"use client";

import { use, useEffect, useState } from "react";
import { AlertTriangle, Download, History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import {
  useReport,
  useReportVersions,
  useUpdateReport,
} from "@/features/reports/hooks/use-reports";
import { reportService } from "@/features/reports/services/report.service";
import { formatDateTime } from "@/lib/date";

export default function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const { data: report, isLoading, isError } = useReport(id);
  const { data: versionsData } = useReportVersions(id);
  const updateReport = useUpdateReport(id);

  const [remarks, setRemarks] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [followUpNotes, setFollowUpNotes] = useState("");

  useEffect(() => {
    if (!report) return;
    setRemarks(report.doctor_remarks ?? "");
    setFollowUpDate(report.follow_up_date ?? "");
    setFollowUpNotes(report.follow_up_notes ?? "");
  }, [report]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (isError || !report) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <AlertTriangle className="h-6 w-6 text-danger" />
          <p className="text-body-lg font-medium text-text-primary">Report not found</p>
        </CardContent>
      </Card>
    );
  }

  const canEdit = user?.role === "doctor";
  const dirty =
    remarks !== (report.doctor_remarks ?? "") ||
    followUpDate !== (report.follow_up_date ?? "") ||
    followUpNotes !== (report.follow_up_notes ?? "");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-h2 text-text-primary">Consultation report</h1>
          <p className="mt-1 text-body text-text-secondary">
            {report.report_type.replace(/_/g, " ")} · Version {report.current_version} · Generated{" "}
            {formatDateTime(report.created_at)}
          </p>
        </div>
        <Button asChild variant="secondary">
          <a href={reportService.downloadUrl(report.id)} target="_blank" rel="noreferrer">
            <Download className="h-4 w-4" /> Download PDF
          </a>
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="overflow-hidden p-0">
          {report.pdf_url ? (
            <iframe
              src={reportService.downloadUrl(report.id)}
              title="Report PDF preview"
              className="h-[75vh] w-full"
            />
          ) : (
            <div className="flex h-96 flex-col items-center justify-center gap-2 p-8 text-center">
              <AlertTriangle className="h-6 w-6 text-text-secondary" />
              <p className="text-body text-text-secondary">
                No PDF has been generated for this report yet.
              </p>
            </div>
          )}
        </Card>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Doctor remarks &amp; follow-up</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-caption font-medium text-text-secondary">Remarks</label>
                <Textarea
                  value={remarks}
                  disabled={!canEdit}
                  onChange={(e) => setRemarks(e.target.value)}
                  rows={4}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-caption font-medium text-text-secondary">
                  Follow-up date
                </label>
                <Input
                  type="date"
                  value={followUpDate}
                  disabled={!canEdit}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-caption font-medium text-text-secondary">
                  Follow-up notes
                </label>
                <Textarea
                  value={followUpNotes}
                  disabled={!canEdit}
                  onChange={(e) => setFollowUpNotes(e.target.value)}
                  rows={2}
                />
              </div>
              {canEdit && (
                <Button
                  size="sm"
                  disabled={!dirty}
                  loading={updateReport.isPending}
                  onClick={() =>
                    updateReport.mutate({
                      doctor_remarks: remarks,
                      follow_up_date: followUpDate || undefined,
                      follow_up_notes: followUpNotes,
                    })
                  }
                >
                  Save &amp; regenerate PDF
                </Button>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-4 w-4" /> Version history
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {(versionsData ?? []).map((version) => (
                <div
                  key={version.id}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                >
                  <div>
                    <Badge variant="outline">v{version.version_number}</Badge>
                    <span className="ml-2 text-caption text-text-secondary">
                      {formatDateTime(version.created_at)}
                    </span>
                  </div>
                  {version.pdf_url && (
                    <a
                      href={reportService.versionDownloadUrl(report.id, version.version_number)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-caption text-primary hover:underline"
                    >
                      View
                    </a>
                  )}
                </div>
              ))}
              {(versionsData ?? []).length === 0 && (
                <p className="text-body text-text-secondary">No version history yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
