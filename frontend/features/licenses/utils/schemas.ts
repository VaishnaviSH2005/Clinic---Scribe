import { z } from "zod";

export const licenseFormSchema = z.object({
  hospital_id: z.string().min(1, "Hospital is required."),
  plan_name: z.string().min(1, "Plan name is required."),
  status: z.enum(["trial", "active", "expired", "cancelled"]),
  starts_at: z.string().min(1, "Start date is required."),
  expires_at: z.string().min(1, "Expiry date is required."),
});
export type LicenseFormValues = z.infer<typeof licenseFormSchema>;
