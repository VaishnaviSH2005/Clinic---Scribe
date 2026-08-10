"use client";

import { SuperAdminHospitals } from "@/features/settings/components/hospitals-tab";

export default function HospitalsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Hospitals</h1>
        <p className="mt-1 text-body text-text-secondary">
          Register and manage hospitals on the platform.
        </p>
      </div>
      <SuperAdminHospitals />
    </div>
  );
}
