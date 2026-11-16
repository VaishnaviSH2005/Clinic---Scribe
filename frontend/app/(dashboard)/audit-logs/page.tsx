"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuditLogTable } from "@/features/audit-logs/components/audit-log-table";

export default function AuditLogsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Audit Logs</h1>
        <p className="mt-1 text-body text-text-secondary">
          Platform-wide record of authentication and administrative events.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          <AuditLogTable showHospital />
        </CardContent>
      </Card>
    </div>
  );
}
