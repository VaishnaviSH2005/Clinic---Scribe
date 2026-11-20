"use client";

import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";
import {
  Activity,
  Building2,
  CalendarClock,
  CalendarX2,
  CheckCircle2,
  FileText,
  KeySquare,
  Sparkles,
  Stethoscope,
  UserPlus,
  Users,
  type LucideIcon,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { HoverLiftCard, Stagger } from "@/components/motion/primitives";
import { Card, CardContent } from "@/components/ui/card";
import type { Analytics, NamedCount, TimeSeriesPoint } from "@/types/analytics";

// Split out from the analytics page so recharts (a large dependency used
// nowhere else in the app) only ships to the client when this component is
// dynamically imported (ssr: false) — keeps every other route's bundle free
// of charting code.

const C = {
  navy: "#1E3A8A",
  blue: "#2563EB",
  teal: "#0F766E",
  green: "#16A34A",
  amber: "#D97706",
  rose: "#DC2626",
  violet: "#7C3AED",
  slate: "#94A3B8",
};

const STATUS_COLORS: Record<string, string> = {
  approved: C.green,
  pending_review: C.amber,
  in_progress: C.blue,
  ai_processing: C.violet,
  draft: C.slate,
  upcoming: C.blue,
  checked_in: C.violet,
  completed: C.green,
  cancelled: C.slate,
  missed: C.rose,
  active: C.green,
  inactive: C.slate,
  suspended: C.rose,
  trial: C.violet,
  expired: C.rose,
};
const FALLBACK_COLORS = [C.blue, C.teal, C.violet, C.amber, C.green, C.rose, C.navy, C.slate];

function colorFor(name: string, index: number): string {
  return STATUS_COLORS[name] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length] ?? C.slate;
}

function labelize(name: string): string {
  const text = name.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function parseDay(value: string): [number, number, number] {
  const [y = 1970, m = 1, d = 1] = value.slice(0, 10).split("-").map(Number);
  return [y, m - 1, d];
}

function shortDate(value: string): string {
  const [y, m, d] = parseDay(value);
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short" }).format(
    new Date(y, m, d),
  );
}

function fullDate(value: string): string {
  const [y, m, d] = parseDay(value);
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(y, m, d));
}

/** The API returns only days that have data; fill the quiet days with real zeros so
 *  trend charts show the whole selected range. Ranges over ~4 months are left as-is. */
function fillDays(points: TimeSeriesPoint[], from: string, to: string): TimeSeriesPoint[] {
  const counts = new Map(points.map((p) => [p.date.slice(0, 10), p.count]));
  const [fy, fm, fd] = parseDay(from);
  const [ty, tm, td] = parseDay(to);
  const start = Date.UTC(fy, fm, fd);
  const end = Date.UTC(ty, tm, td);
  const dayMs = 86_400_000;
  if (!(end >= start) || (end - start) / dayMs > 120) {
    return [...points].sort((a, b) => a.date.localeCompare(b.date));
  }
  const out: TimeSeriesPoint[] = [];
  for (let t = start; t <= end; t += dayMs) {
    const key = new Date(t).toISOString().slice(0, 10);
    out.push({ date: key, count: counts.get(key) ?? 0 });
  }
  return out;
}

// ---------------------------------------------------------------- building blocks

function CountUp({
  value,
  decimals = 0,
  suffix = "",
}: {
  value: number;
  decimals?: number;
  suffix?: string;
}) {
  const motionValue = useMotionValue(0);
  const text = useTransform(motionValue, (v) => `${v.toFixed(decimals)}${suffix}`);

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      motionValue.set(value);
      return;
    }
    const controls = animate(motionValue, value, { duration: 0.9, ease: "easeOut" });
    return () => controls.stop();
  }, [motionValue, value]);

  return <motion.span>{text}</motion.span>;
}

function Sparkline({ data, color, id }: { data: TimeSeriesPoint[]; color: string; id: string }) {
  if (data.length < 2) return <div className="h-11" />;
  return (
    <div className="h-11 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.4} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="count"
            stroke={color}
            strokeWidth={2}
            fill={`url(#spark-${id})`}
            dot={false}
            isAnimationActive
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function ChartTooltip({
  active,
  payload,
  label,
  unit,
  dateLabel,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ value?: number | string; name?: string | number; color?: string }>;
  label?: string | number;
  unit: string;
  dateLabel?: boolean;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const item = payload[0];
  if (!item) return null;
  const title = dateLabel && typeof label === "string" ? fullDate(label) : (item.name ?? label);
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 shadow-level-3">
      <p className="text-caption text-text-secondary">{title}</p>
      <p className="text-body font-semibold text-text-primary">
        {item.value} <span className="font-normal text-text-secondary">{unit}</span>
      </p>
    </div>
  );
}

function EmptyState({ message = "No data for this range." }: { message?: string }) {
  return (
    <div className="flex h-52 flex-col items-center justify-center gap-2 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-background text-text-secondary">
        <Activity className="h-5 w-5" />
      </span>
      <p className="text-body text-text-secondary">{message}</p>
      <p className="text-caption text-disabled">Try a wider date range.</p>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  icon: Icon,
  accent,
  className,
  children,
}: {
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  accent: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <HoverLiftCard className={className}>
      <Card className="relative h-full overflow-hidden">
        <div
          className="absolute inset-x-0 top-0 h-1"
          style={{ background: `linear-gradient(90deg, ${accent}, ${accent}33)` }}
        />
        <div className="mb-4 flex items-center gap-3">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-md"
            style={{ background: `${accent}1A`, color: accent }}
          >
            <Icon className="h-5 w-5" />
          </span>
          <div>
            <h3 className="text-h5 text-text-primary">{title}</h3>
            {subtitle ? <p className="text-caption text-text-secondary">{subtitle}</p> : null}
          </div>
        </div>
        <CardContent>{children}</CardContent>
      </Card>
    </HoverLiftCard>
  );
}

function KpiCard({
  label,
  value,
  decimals,
  suffix,
  hint,
  icon: Icon,
  color,
  trend,
  id,
}: {
  label: string;
  value: number;
  decimals?: number;
  suffix?: string;
  hint: string;
  icon: LucideIcon;
  color: string;
  trend?: TimeSeriesPoint[];
  id: string;
}) {
  return (
    <HoverLiftCard>
      <Card className="relative h-full overflow-hidden">
        <Icon
          className="pointer-events-none absolute -right-3 -top-3 h-24 w-24 opacity-[0.06]"
          style={{ color }}
        />
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-caption font-medium uppercase tracking-wide text-text-secondary">
              {label}
            </p>
            <p className="mt-2 text-h1 text-text-primary">
              <CountUp value={value} decimals={decimals} suffix={suffix} />
            </p>
          </div>
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-white shadow-level-2"
            style={{ background: `linear-gradient(135deg, ${color}, ${color}B3)` }}
          >
            <Icon className="h-5 w-5" />
          </span>
        </div>
        <p className="mt-1 text-caption text-text-secondary">{hint}</p>
        {trend ? (
          <div className="mt-3">
            <Sparkline data={trend} color={color} id={id} />
          </div>
        ) : null}
      </Card>
    </HoverLiftCard>
  );
}

function DonutCard({
  title,
  subtitle,
  icon,
  accent,
  data,
  totalLabel,
  className,
}: {
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  accent: string;
  data: NamedCount[];
  totalLabel: string;
  className?: string;
}) {
  const slices = data
    .filter((d) => d.count > 0)
    .map((d, i) => ({
      key: d.name,
      name: labelize(d.name),
      count: d.count,
      color: colorFor(d.name, i),
    }));
  const total = sum(slices.map((s) => s.count));

  return (
    <ChartCard title={title} subtitle={subtitle} icon={icon} accent={accent} className={className}>
      {total === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-4">
          <div className="relative h-44 w-44 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={slices}
                  dataKey="count"
                  nameKey="name"
                  innerRadius={56}
                  outerRadius={80}
                  paddingAngle={slices.length > 1 ? 3 : 0}
                  cornerRadius={6}
                  stroke="none"
                >
                  {slices.map((s) => (
                    <Cell key={s.key} fill={s.color} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip unit="total" />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-h3 text-text-primary">
                <CountUp value={total} />
              </span>
              <span className="text-caption text-text-secondary">{totalLabel}</span>
            </div>
          </div>
          <ul className="flex min-w-[140px] flex-1 flex-col gap-2">
            {slices.map((s) => (
              <li key={s.key} className="flex items-center gap-2 text-body">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ background: s.color }}
                />
                <span className="flex-1 text-text-primary">{s.name}</span>
                <span className="font-semibold text-text-primary">{s.count}</span>
                <span className="w-10 text-right text-caption text-text-secondary">
                  {Math.round((s.count / total) * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </ChartCard>
  );
}

function RankedBarsCard({
  title,
  subtitle,
  icon,
  accent,
  data,
  unit,
}: {
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  accent: string;
  data: NamedCount[];
  unit: string;
}) {
  const rows = [...data].sort((a, b) => b.count - a.count).slice(0, 8);
  return (
    <ChartCard title={title} subtitle={subtitle} icon={icon} accent={accent}>
      {rows.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={{ height: Math.max(190, rows.length * 44) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: 0, right: 36, left: 0, bottom: 0 }}
            >
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                width={128}
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="#374151"
                tickFormatter={(v: string) => (v.length > 18 ? `${v.slice(0, 17)}…` : v)}
              />
              <Tooltip cursor={{ fill: "#F1F5F9" }} content={<ChartTooltip unit={unit} />} />
              <Bar dataKey="count" radius={[0, 8, 8, 0]} barSize={20}>
                {rows.map((row, i) => (
                  <Cell key={row.name} fill={FALLBACK_COLORS[i % FALLBACK_COLORS.length]} />
                ))}
                <LabelList dataKey="count" position="right" fontSize={12} fill="#111827" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </ChartCard>
  );
}

// ---------------------------------------------------------------- dashboard

export function AnalyticsCharts({
  data,
  isPlatform,
  isDoctor,
}: {
  data: Analytics;
  isPlatform: boolean;
  isDoctor: boolean;
}) {
  const consultations = fillDays(data.consultations_per_day, data.date_from, data.date_to);
  const newPatients = fillDays(data.new_patients_per_day, data.date_from, data.date_to);

  const totalConsultations = sum(Object.values(data.consultations_by_status));
  const approved = data.consultations_by_status.approved ?? 0;
  const newPatientsTotal = sum(data.new_patients_per_day.map((p) => p.count));
  const aiCompleted = data.ai_processing_outcomes.ai_pipeline_completed ?? 0;
  const aiFailed = data.ai_processing_outcomes.ai_stage_failed ?? 0;
  const toNamed = (record: Record<string, number>): NamedCount[] =>
    Object.entries(record).map(([name, count]) => ({ name, count }));

  return (
    <div className="flex flex-col gap-6">
      <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" step={0.06}>
        <KpiCard
          id="consultations"
          label="Consultations"
          value={totalConsultations}
          hint={`${approved} approved by doctors`}
          icon={Stethoscope}
          color={C.blue}
          trend={consultations}
        />
        {isDoctor ? (
          <KpiCard
            id="approved"
            label="Approved notes"
            value={approved}
            hint="Reviewed and signed off"
            icon={CheckCircle2}
            color={C.green}
          />
        ) : (
          <KpiCard
            id="patients"
            label="New patients"
            value={newPatientsTotal}
            hint="Registered in this period"
            icon={UserPlus}
            color={C.teal}
            trend={newPatients}
          />
        )}
        <KpiCard
          id="reports"
          label="Reports generated"
          value={data.reports_generated}
          hint="PDF consultation reports"
          icon={FileText}
          color={C.violet}
        />
        {isDoctor ? (
          <KpiCard
            id="pending"
            label="Awaiting review"
            value={data.consultations_by_status.pending_review ?? 0}
            hint="AI notes waiting for your approval"
            icon={Sparkles}
            color={C.amber}
          />
        ) : (
          <KpiCard
            id="missed"
            label="Missed appointments"
            value={data.missed_appointment_rate}
            decimals={data.missed_appointment_rate % 1 === 0 ? 0 : 1}
            suffix="%"
            hint={`AI pipeline: ${aiCompleted} completed, ${aiFailed} stage failures`}
            icon={CalendarX2}
            color={data.missed_appointment_rate > 20 ? C.rose : C.amber}
          />
        )}
      </Stagger>

      <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-3" step={0.06} delay={0.1}>
        <ChartCard
          title="Consultations per day"
          subtitle="Daily activity across the selected period"
          icon={Activity}
          accent={C.blue}
          className="lg:col-span-2"
        >
          {consultations.length === 0 ? (
            <EmptyState />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={consultations} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="grad-consultations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={C.blue} stopOpacity={0.45} />
                    <stop offset="100%" stopColor={C.blue} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={shortDate}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  minTickGap={28}
                  stroke="#6B7280"
                />
                <YAxis
                  allowDecimals={false}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  stroke="#6B7280"
                />
                <Tooltip
                  cursor={{ stroke: C.blue, strokeDasharray: "4 4" }}
                  content={<ChartTooltip unit="consultations" dateLabel />}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke={C.blue}
                  strokeWidth={3}
                  fill="url(#grad-consultations)"
                  activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <DonutCard
          title="Consultation status"
          subtitle="Where each consultation stands"
          icon={Stethoscope}
          accent={C.violet}
          data={toNamed(data.consultations_by_status)}
          totalLabel="total"
        />
      </Stagger>

      <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-3" step={0.06} delay={0.15}>
        {isDoctor ? null : (
          <ChartCard
            title="New patients per day"
            subtitle="Patients registered at reception"
            icon={UserPlus}
            accent={C.teal}
            className="lg:col-span-2"
          >
            {newPatients.length === 0 ? (
              <EmptyState />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={newPatients} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="grad-patients" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={C.teal} stopOpacity={1} />
                      <stop offset="100%" stopColor={C.teal} stopOpacity={0.35} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={shortDate}
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={28}
                    stroke="#6B7280"
                  />
                  <YAxis
                    allowDecimals={false}
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    stroke="#6B7280"
                  />
                  <Tooltip
                    cursor={{ fill: "#F1F5F9" }}
                    content={<ChartTooltip unit="new patients" dateLabel />}
                  />
                  <Bar
                    dataKey="count"
                    fill="url(#grad-patients)"
                    radius={[8, 8, 0, 0]}
                    maxBarSize={32}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        )}
        <DonutCard
          title="Appointments"
          subtitle="Outcome of scheduled visits"
          icon={CalendarClock}
          accent={C.amber}
          data={toNamed(data.appointments_by_status)}
          totalLabel="visits"
          className={isDoctor ? "lg:col-span-3" : undefined}
        />
      </Stagger>

      {isPlatform ? (
        <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-3" step={0.06} delay={0.2}>
          <RankedBarsCard
            title="Consultations by hospital"
            subtitle="Most active hospitals"
            icon={Building2}
            accent={C.navy}
            data={data.consultations_by_hospital}
            unit="consultations"
          />
          <DonutCard
            title="Hospitals"
            subtitle="By account status"
            icon={Building2}
            accent={C.green}
            data={toNamed(data.hospitals_by_status)}
            totalLabel="hospitals"
          />
          <DonutCard
            title="Licenses"
            subtitle="By subscription status"
            icon={KeySquare}
            accent={C.violet}
            data={toNamed(data.licenses_by_status)}
            totalLabel="licenses"
          />
        </Stagger>
      ) : isDoctor ? null : (
        <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-2" step={0.06} delay={0.2}>
          <RankedBarsCard
            title="Consultations by doctor"
            subtitle="Workload across your clinicians"
            icon={Users}
            accent={C.blue}
            data={data.consultations_by_doctor}
            unit="consultations"
          />
          <RankedBarsCard
            title="Consultations by department"
            subtitle="Busiest departments"
            icon={Building2}
            accent={C.teal}
            data={data.consultations_by_department}
            unit="consultations"
          />
        </Stagger>
      )}
    </div>
  );
}
