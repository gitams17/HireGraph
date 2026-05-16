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
