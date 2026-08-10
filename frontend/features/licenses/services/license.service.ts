import { apiClient } from "@/lib/api-client";
import type { Subscription, SubscriptionCreatePayload, SubscriptionUpdatePayload } from "@/types/subscription";

export const licenseService = {
  list: (page: number, pageSize: number) =>
    apiClient.getList<Subscription>(`/subscriptions?page=${page}&pageSize=${pageSize}`),
  create: (payload: SubscriptionCreatePayload) => apiClient.post<Subscription>("/subscriptions", payload),
  update: (id: string, payload: SubscriptionUpdatePayload) =>
    apiClient.patch<Subscription>(`/subscriptions/${id}`, payload),
};
