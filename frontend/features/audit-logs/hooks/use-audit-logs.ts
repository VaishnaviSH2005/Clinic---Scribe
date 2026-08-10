"use client";

import { useQuery } from "@tanstack/react-query";

import { auditLogService } from "../services/audit-log.service";

export function useAuditLogs(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["audit-logs", page, pageSize],
    queryFn: () => auditLogService.list(page, pageSize),
  });
}
