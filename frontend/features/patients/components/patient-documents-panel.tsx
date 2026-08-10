"use client";

import { useRef } from "react";
import { Download, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFileSize } from "@/lib/format";
import { formatDate } from "@/lib/date";

import { usePatientDetailMutations, usePatientDocuments } from "../hooks/use-patient-detail";
import { patientService } from "../services/patient.service";

export function PatientDocumentsPanel({ patientId }: { patientId: string }) {
  const { data: documents, isLoading } = usePatientDocuments(patientId);
  const { uploadDocument } = usePatientDetailMutations(patientId);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadDocument.mutate({ file });
    e.target.value = "";
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Documents</CardTitle>
        <Button
          size="sm"
          loading={uploadDocument.isPending}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-4 w-4" /> Upload document
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          className="hidden"
          onChange={handleFileChange}
        />
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {!isLoading && documents?.length === 0 && (
          <p className="text-body text-text-secondary">No medical documents uploaded.</p>
        )}
        {!isLoading && documents && documents.length > 0 && (
          <ul className="flex flex-col divide-y divide-border">
            {documents.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-body font-medium text-text-primary">{doc.file_name}</p>
                  <p className="text-caption text-text-secondary">
                    {doc.document_category ?? "Document"} · {formatFileSize(doc.file_size_bytes)} ·{" "}
                    {formatDate(doc.created_at)}
                  </p>
                </div>
                <a
                  href={patientService.documentDownloadUrl(patientId, doc.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-body text-primary hover:underline"
                >
                  <Download className="h-4 w-4" /> Download
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
