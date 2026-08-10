import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Users,
  CalendarClock,
  Stethoscope,
  FileText,
  BarChart3,
  Settings,
  Building2,
  KeySquare,
  ScrollText,
} from "lucide-react";

import { ROLES, type Role } from "./roles";
import { ROUTES } from "./routes";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  roles: Role[];
}

// Main sidebar navigation (PRD Ch6.4), gated by the Access Control Matrix
// (Ch6.15). This is a UX convenience only — the backend re-enforces every
// permission independently (Ch18).
export const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: ROUTES.dashboard,
    icon: LayoutDashboard,
    roles: [ROLES.superAdmin, ROLES.hospitalAdmin, ROLES.doctor, ROLES.receptionist],
  },
  {
    label: "Hospitals",
    href: ROUTES.hospitals,
    icon: Building2,
    roles: [ROLES.superAdmin],
  },
  {
    label: "Licenses",
    href: ROUTES.licenses,
    icon: KeySquare,
    roles: [ROLES.superAdmin],
  },
  {
    label: "Audit Logs",
    href: ROUTES.auditLogs,
    icon: ScrollText,
    roles: [ROLES.superAdmin],
  },
  {
    label: "Patients",
    href: ROUTES.patients,
    icon: Users,
    roles: [ROLES.superAdmin, ROLES.hospitalAdmin, ROLES.doctor, ROLES.receptionist],
  },
  {
    label: "Appointments",
    href: ROUTES.appointments,
    icon: CalendarClock,
    roles: [ROLES.hospitalAdmin, ROLES.doctor, ROLES.receptionist],
  },
  {
    label: "Consultations",
    href: ROUTES.consultations,
    icon: Stethoscope,
    roles: [ROLES.doctor],
  },
  {
    label: "Reports",
    href: ROUTES.reports,
    icon: FileText,
    roles: [ROLES.hospitalAdmin, ROLES.doctor],
  },
  {
    label: "Analytics",
    href: ROUTES.analytics,
    icon: BarChart3,
    roles: [ROLES.hospitalAdmin, ROLES.doctor],
  },
  {
    label: "Settings",
    href: ROUTES.settings,
    icon: Settings,
    roles: [ROLES.superAdmin, ROLES.hospitalAdmin, ROLES.doctor, ROLES.receptionist],
  },
];
