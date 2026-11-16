"use client";

import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowRight } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HoverLiftCard, Stagger, StaggerItem } from "@/components/motion/primitives";
import { Skeleton } from "@/components/ui/skeleton";
import { ROUTES } from "@/constants/routes";
import { useDashboard } from "@/features/dashboard/hooks/use-dashboard";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import { formatDateTime } from "@/lib/date";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useDashboard();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <AlertTriangle className="h-6 w-6 text-danger" />
          <p className="text-body-lg font-medium text-text-primary">Unable to load dashboard</p>
          <p className="text-body text-text-secondary">Please try again in a moment.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">
          Welcome back{user ? `, ${user.name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-1 text-body text-text-secondary">Here is what&apos;s happening today.</p>
      </div>

      <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" step={0.04}>
        {data.cards.map((card) => (
          <HoverLiftCard key={card.key}>
            <Card className="h-full transition-shadow duration-card hover:shadow-level-3">
              <CardContent className="py-5">
                <p className="text-caption font-medium uppercase text-text-secondary">
                  {card.label}
                </p>
                <p className="mt-2 text-h2 text-text-primary">{card.value}</p>
                {card.hint && <p className="mt-1 text-caption text-text-secondary">{card.hint}</p>}
              </CardContent>
            </Card>
          </HoverLiftCard>
        ))}
        {data.cards.length === 0 && (
          <p className="text-body text-text-secondary">
            No summary data is available for your account yet.
          </p>
        )}
      </Stagger>

      {data.appointments_today.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Today&apos;s appointments</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => router.push(ROUTES.appointments)}>
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </CardHeader>
          <CardContent>
            <Stagger className="flex flex-col gap-2" step={0.04} delay={0.1}>
              {data.appointments_today.map((appt) => (
                <StaggerItem
                  key={appt.id}
                  className="hover:bg-muted flex items-center justify-between rounded-md border border-border px-4 py-3 transition-colors duration-micro"
                >
                  <div>
                    <p className="text-body font-medium text-text-primary">{appt.patient_name}</p>
                    <p className="text-caption text-text-secondary">
                      {formatDateTime(appt.scheduled_at)}
                    </p>
                  </div>
                  <StatusBadge status={appt.status} />
                </StaggerItem>
              ))}
            </Stagger>
          </CardContent>
        </Card>
      )}

      {data.recent_consultations.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent consultations</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => router.push(ROUTES.consultations)}>
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </CardHeader>
          <CardContent>
            <Stagger className="flex flex-col gap-2" step={0.04} delay={0.1}>
              {data.recent_consultations.map((c) => (
                <StaggerItem
                  key={c.id}
                  className="hover:bg-muted flex items-center justify-between rounded-md border border-border px-4 py-3 transition-colors duration-micro"
                >
                  <div>
                    <p className="text-body font-medium text-text-primary">{c.patient_name}</p>
                    <p className="text-caption text-text-secondary">
                      {formatDateTime(c.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={c.status} />
                </StaggerItem>
              ))}
            </Stagger>
          </CardContent>
        </Card>
      )}

      {data.cards.length > 0 &&
        data.appointments_today.length === 0 &&
        data.recent_consultations.length === 0 && (
          <Card>
            <CardContent className="py-10 text-center text-body text-text-secondary">
              No recent activity to show yet.
            </CardContent>
          </Card>
        )}
    </div>
  );
}
