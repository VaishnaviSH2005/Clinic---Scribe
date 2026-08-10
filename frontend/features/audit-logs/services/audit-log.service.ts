import { apiClient } from "@/lib/api-client";
import type { AuditLog } from "@/types/audit-log";

export const auditLogService = {
  list: (page: number, pageSize: number) =>
    apiClient.getList<AuditLog>(`/audit-logs?page=${page}&pageSize=${pageSize}`),
};
