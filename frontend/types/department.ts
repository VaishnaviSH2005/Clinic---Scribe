export type DepartmentStatus = "active" | "inactive";

export interface Department {
  id: string;
  hospital_id: string;
  name: string;
  head_of_department_id: string | null;
  status: DepartmentStatus;
}

export interface DepartmentCreatePayload {
  name: string;
  head_of_department_id?: string;
}

export interface DepartmentUpdatePayload {
  name?: string;
  head_of_department_id?: string;
}
