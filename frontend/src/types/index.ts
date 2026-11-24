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
  latest_analysis?: ResumeAnalysis | null;
  events?: ApplicationEvent[];
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Phase 6: AI-Powered Resume Screening
// ---------------------------------------------------------------------------

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";

export interface SkillEvidenceItem {
  skill: string;
  status: "found" | "partial" | "missing";
  evidence: string;
}

export interface CandidateAssessment {
  ats_score: number;
  summary_headline: string;
  required_skills_evaluation: SkillEvidenceItem[];
  relevant_experience_summary: string;
  missing_evidence: string[];
  strengths: string[];
  concerns_or_gaps: string[];
  reviewer_recommendation:
    | "strong_match"
    | "potential_match"
    | "requires_human_review"
    | "does_not_meet_minimum";
  recommendation_rationale: string;
}

export interface EducationItem {
  institution: string;
  degree: string;
  field_of_study: string;
  start_year?: number | null;
  end_year?: number | null;
  grade_or_gpa?: string | null;
}

export interface ExperienceItem {
  company: string;
  title: string;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  description: string;
  technologies_used: string[];
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies: string[];
  url?: string | null;
}

export interface CertificationItem {
  name: string;
  issuer: string;
  issue_year?: number | null;
}

export interface ParsedResume {
  candidate_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  summary: string;
  technical_skills: string[];
  soft_skills: string[];
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
}

export interface ResumeAnalysis {
  id: string;
  application_id: string;
  resume_id: string;
  model_name: string;
  prompt_version: string;
  evaluation_rubric_version: string;
  extracted_data: ParsedResume;
  assessment: CandidateAssessment;
  ats_score: number | null;
  recruiter_feedback?: Record<string, any>;
  status: AnalysisStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Phase 7: Interview Management
// ---------------------------------------------------------------------------

export type InterviewType = "technical" | "hr" | "managerial" | "screening" | "culture_fit";

export type InterviewStatus = "scheduled" | "completed" | "cancelled" | "rescheduled";

export type ParticipantRole = "lead" | "interviewer" | "observer" | "scribe";

export type ParticipantStatus = "invited" | "accepted" | "declined" | "tentative";

export type Recommendation = "strong_hire" | "hire" | "neutral" | "no_hire" | "strong_no_hire";

export interface PreparedQuestion {
  id: string;
  question: string;
  category: string;
  notes?: string;
  evaluation_criteria?: string;
}

export interface QuestionScore {
  question_id: string;
  score: number;
  notes: string;
}

export interface InterviewParticipant {
  id: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
  };
  role: ParticipantRole;
  status: ParticipantStatus;
  created_at: string;
}

export interface InterviewFeedback {
  id: string;
  interview: string;
  interviewer: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
  };
  rating: number;
  recommendation: Recommendation;
  summary: string;
  strengths: string;
  areas_for_improvement: string;
  question_scores: QuestionScore[];
  submitted_at: string;
  updated_at: string;
}

export interface InterviewTemplate {
  id: string;
  organization: string;
  name: string;
  interview_type: InterviewType;
  description: string;
  default_duration_minutes: number;
  default_questions: PreparedQuestion[];
  created_by?: {
    id: string;
    email: string;
    full_name: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface InterviewListItem {
  id: string;
  organization: string;
  application_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  job_id: string;
  job_title: string;
  template?: string | null;
  title: string;
  interview_type: InterviewType;
  status: InterviewStatus;
  scheduled_start: string;
  scheduled_end: string;
  location_type: string;
  meeting_link?: string;
  location_details?: string;
  participants: InterviewParticipant[];
  feedbacks_count: number;
  created_at: string;
  updated_at: string;
}

export interface InterviewDetail {
  id: string;
  organization: string;
  application: {
    id: string;
    stage: string;
    candidate: {
      id: string;
      full_name: string;
      email: string;
      phone?: string;
      linkedin_url?: string;
      github_url?: string;
    };
    job: {
      id: string;
      title: string;
      department: string;
      required_skills: string[];
      responsibilities: string[];
    };
    resume?: {
      id: string;
      file_name: string;
    } | null;
    latest_analysis?: {
      id: string;
      ats_score: number | null;
      summary_headline: string;
    } | null;
  };
  template?: string | null;
  title: string;
  interview_type: InterviewType;
  status: InterviewStatus;
  scheduled_start: string;
  scheduled_end: string;
  location_type: string;
  meeting_link: string;
  location_details: string;
  prepared_questions: PreparedQuestion[];
  notes: string;
  participants: InterviewParticipant[];
  feedbacks: InterviewFeedback[];
  created_by?: {
    id: string;
    email: string;
    full_name: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface SuggestedQuestion {
  id: string;
  question: string;
  category: string;
  evaluation_criteria: string;
  follow_up_hint?: string;
}

export interface SuggestedQuestionsResponse {
  technical_questions: SuggestedQuestion[];
  behavioural_questions: SuggestedQuestion[];
  project_questions: SuggestedQuestion[];
  competency_questions: SuggestedQuestion[];
}

// ---------------------------------------------------------------------------
// Phase 8: Advanced Workflow Automation
// ---------------------------------------------------------------------------

export type WorkflowExecutionStatus = "running" | "interrupted" | "completed" | "failed";

export interface WorkflowEventItem {
  id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface WorkflowExecutionDetail {
  id: string;
  thread_id: string;
  organization?: string;
  job_id: string;
  job_title?: string;
  application?: string | null;
  candidate_name?: string | null;
  workflow_type: string;
  status: WorkflowExecutionStatus;
  current_step: string;
  error_message: string;
  state_snapshot?: Record<string, any>;
  retry_count: number;
  last_retried_at?: string | null;
  started_at: string;
  completed_at?: string | null;
  events?: WorkflowEventItem[];
}

export interface WorkflowDashboardMetrics {
  total_executions: number;
  active_count: number;
  pending_approvals_count: number;
  failed_count: number;
  completed_count: number;
  recent_events: {
    id: string;
    thread_id: string;
    job_title: string;
    event_type: string;
    payload: Record<string, any>;
    created_at: string;
  }[];
}

export interface JobOffer {
  id: string;
  organization: string;
  application: string;
  candidate_name?: string;
  candidate_email?: string;
  job_title?: string;
  base_salary: number;
  currency: string;
  equity: string;
  sign_on_bonus?: number | null;
  start_date: string;
  status: string;
  candidate_response?: string;
  negotiation_notes?: string;
  counter_salary?: number | null;
  terms: string;
  approved_by?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OnboardingChecklistTask {
  id: string;
  organization: string;
  application: string;
  candidate_name?: string;
  title: string;
  category: "compliance" | "it_setup" | "hr_paperwork" | "team_intro";
  status: "pending" | "in_progress" | "completed" | "skipped";
  due_date?: string | null;
  assigned_to?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface JobBoardPublication {
  id: string;
  job: string;
  job_title?: string;
  board_name: string;
  external_id: string;
  status: "pending" | "published" | "failed" | "expired";
  posting_url: string;
  payload: Record<string, any>;
  published_at?: string | null;
  created_at: string;
}





