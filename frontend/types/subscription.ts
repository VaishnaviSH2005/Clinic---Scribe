export type SubscriptionStatus = "trial" | "active" | "expired" | "cancelled";

export interface Subscription {
  id: string;
  hospital_id: string;
  plan_name: string;
  status: SubscriptionStatus;
  starts_at: string;
  expires_at: string;
}

export interface SubscriptionCreatePayload {
  hospital_id: string;
  plan_name: string;
  status: SubscriptionStatus;
  starts_at: string;
  expires_at: string;
}

export interface SubscriptionUpdatePayload {
  plan_name?: string;
  status?: SubscriptionStatus;
  starts_at?: string;
  expires_at?: string;
}
