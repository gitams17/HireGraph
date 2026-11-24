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

// ---------------------------------------------------------------------------
// Phase 4: Job Description Versioning, Approvals, & Workflows
// ---------------------------------------------------------------------------

export type VersionStatus = "draft" | "pending_approval" | "approved" | "rejected";
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type WorkflowStatus = "running" | "interrupted" | "completed" | "failed";

export const VERSION_STATUS_LABELS: Record<VersionStatus, string> = {
  draft: "Draft",
  pending_approval: "Pending Approval",
  approved: "Approved",
  rejected: "Rejected",
};

export const APPROVAL_STATUS_LABELS: Record<ApprovalStatus, string> = {
  pending: "Pending Review",
  approved: "Approved",
  rejected: "Rejected",
};

export interface JobDescriptionVersion {
  id: string;
  job_id: string;
  version_number: number;
  title: string;
  overview: string;
  responsibilities: string[];
  required_qualifications: string[];
  preferred_qualifications: string[];
  benefits: string[];
  raw_content: string;
  status: VersionStatus;
  created_by: User | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRequest {
  id: string;
  organization: string;
  job_id: string;
  job_title: string;
  version_id: string;
  version_number: number;
  status: ApprovalStatus;
  requested_by: User;
  reviewed_by: User | null;
  feedback: string;
  created_at: string;
  decided_at: string | null;
}

export interface WorkflowEvent {
  id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface WorkflowExecution {
  id: string;
  thread_id: string;
  job_id: string;
  workflow_type: string;
  status: WorkflowStatus;
  current_step: string;
  error_message: string;
  started_at: string;
  completed_at: string | null;
  events: WorkflowEvent[];
}

// ---------------------------------------------------------------------------
// Phase 5: Candidate Management and Application Tracking
// ---------------------------------------------------------------------------

export type ApplicationStage =
  | "applied"
  | "under_review"
  | "shortlisted"
  | "interview"
  | "selected"
  | "rejected";

export const STAGE_LABELS: Record<ApplicationStage, string> = {
  applied: "Applied",
  under_review: "Under Review",
  shortlisted: "Shortlisted",
  interview: "Interview",
  selected: "Selected",
  rejected: "Rejected",
};

export const STAGE_ORDER: ApplicationStage[] = [
  "applied",
  "under_review",
  "shortlisted",
  "interview",
  "selected",
  "rejected",
];

export const STAGE_COLORS: Record<ApplicationStage, string> = {
  applied: "bg-blue-50 text-blue-700 border-blue-200",
  under_review: "bg-amber-50 text-amber-700 border-amber-200",
  shortlisted: "bg-purple-50 text-purple-700 border-purple-200",
  interview: "bg-indigo-50 text-indigo-700 border-indigo-200",
  selected: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export interface Resume {
  id: string;
  candidate_id: string;
  file_name: string;
  file_size: number;
  content_type: string;
  is_primary: boolean;
  download_url: string;
  uploaded_by_name: string | null;
  created_at: string;
}

export interface Candidate {
  id: string;
  organization: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  location: string;
  current_company: string;
  current_title: string;
  total_experience_years: number | null;
  skills: string[];
  notes: string;
  resumes?: Resume[];
  applications?: {
    id: string;
    job_id: string;
    job_title: string;
    stage: ApplicationStage;
    created_at: string;
  }[];
  resume_count?: number;
  application_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ApplicationEvent {
  id: string;
  application_id: string;
  event_type: string;
  from_stage: string;
  to_stage: string;
  notes: string;
  actor_name: string | null;
  created_at: string;
}

export interface Application {
  id: string;
  organization_id: string;
  job_id: string;
  job_title: string;
  job_department: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_company: string;
  candidate_title: string;
  stage: ApplicationStage;
  rating: number | null;
  rejection_reason?: string;
  notes?: string;
  has_resume: boolean;
  candidate?: {
    id: string;
    full_name: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    current_company: string;
    current_title: string;
    location: string;
    skills: string[];
  };
  job?: {
    id: string;
    title: string;
    department: string;
    location: string;
    status: string;
  };
  resume?: Resume | null;
  events?: ApplicationEvent[];
  created_at: string;
  updated_at: string;
}


