// Shared TypeScript types for the HireGraph frontend.

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_joined: string;
}

export type OrganizationRole =
  | "owner"
  | "admin"
  | "recruiter"
  | "hiring_manager"
  | "interviewer";

export const ROLE_LABELS: Record<OrganizationRole, string> = {
  owner: "Owner",
  admin: "Admin",
  recruiter: "Recruiter",
  hiring_manager: "Hiring Manager",
  interviewer: "Interviewer",
};

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
  created_by: User;
  member_count: number;
  current_user_role: OrganizationRole | null;
}

export interface OrganizationMembership {
  id: string;
  user: User;
  role: OrganizationRole;
  joined_at: string;
  is_active: boolean;
}

export interface OrganizationInvitation {
  id: string;
  email: string;
  role: OrganizationRole;
  invited_by: User;
  token: string;
  created_at: string;
  accepted_at: string | null;
  expires_at: string;
  is_expired: boolean;
  is_accepted: boolean;
}

// Generic API error shape returned by DRF
export interface ApiError {
  status: number;
  data: Record<string, string | string[]> & { detail?: string; non_field_errors?: string[] };
}

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

export type JobStatus = "draft" | "open" | "paused" | "closed";
export type EmploymentType = "full_time" | "part_time" | "contract" | "internship";

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  draft: "Draft",
  open: "Open",
  paused: "Paused",
  closed: "Closed",
};

export const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  internship: "Internship",
};

export interface JobRequisition {
  id: string;
  organization: string; // UUID
  title: string;
  department: string;
  location: string;
  employment_type: EmploymentType;
  experience_min: number | null;
  experience_max: number | null;
  required_skills: string[];
  responsibilities: string[];
  status: JobStatus;
  created_by: User;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
