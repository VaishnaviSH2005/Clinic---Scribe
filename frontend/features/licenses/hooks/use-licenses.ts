"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { SubscriptionCreatePayload, SubscriptionStatus } from "@/types/subscription";

import { licenseService } from "../services/license.service";

export function useLicenses(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["licenses", page, pageSize],
    queryFn: () => licenseService.list(page, pageSize),
  });
}

export function useLicenseMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["licenses"] });

  const create = useMutation({
    mutationFn: (payload: SubscriptionCreatePayload) => licenseService.create(payload),
    onSuccess: () => {
      toast.success("License created successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to create license. Please try again."),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: SubscriptionStatus }) =>
      licenseService.update(id, { status }),
    onSuccess: () => {
      toast.success("License status updated successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to update license status."),
  });

  return { create, updateStatus };
}
