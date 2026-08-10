"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/date";
import type { TimeSeriesPoint } from "@/types/analytics";

const CHART_COLOR = "#1E3A8A";
const ACCENT_COLOR = "#0F766E";

function EmptyChart() {
  return (
    <div className="flex h-52 items-center justify-center text-body text-text-secondary">
      No data for this range.
    </div>
  );
}

// Split out from the analytics page so recharts (a large dependency used
// nowhere else in the app) only ships to the client when this component is
// dynamically imported (ssr: false) — keeps every other route's bundle free
// of charting code.
export function AnalyticsCharts({
  consultationsPerDay,
  newPatientsPerDay,
}: {
  consultationsPerDay: TimeSeriesPoint[];
  newPatientsPerDay: TimeSeriesPoint[];
}) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Consultations per day</CardTitle>
        </CardHeader>
        <CardContent>
          {consultationsPerDay.length === 0 ? (
            <EmptyChart />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={consultationsPerDay}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" tickFormatter={(v) => formatDate(v)} fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip labelFormatter={(v) => formatDate(v as string)} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={CHART_COLOR}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>New patients per day</CardTitle>
        </CardHeader>
        <CardContent>
          {newPatientsPerDay.length === 0 ? (
            <EmptyChart />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={newPatientsPerDay}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" tickFormatter={(v) => formatDate(v)} fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip labelFormatter={(v) => formatDate(v as string)} />
                <Bar dataKey="count" fill={ACCENT_COLOR} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
