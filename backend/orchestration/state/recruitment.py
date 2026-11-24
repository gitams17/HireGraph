from typing import Any, Literal, TypedDict


class RecruitmentWorkflowState(TypedDict, total=False):
    # Identifiers
    job_id: str
    organization_id: str
    user_id: str | None
    thread_id: str

    # Status & Diagnostics
    status: Literal["running", "interrupted", "completed", "failed"]
    error: str | None
    current_step: str
    retry_count: int

    # JD Generation & Revision loop
    version_id: str | None
    version_number: int | None
    revision_count: int
    decision: Literal["approved", "rejected"] | None
    feedback: str | None
    approval_request_id: str | None

    # Publication & Monitoring
    published_boards: list[str]
    minimum_applicants: int
    applicant_count: int
    applicant_monitoring_passed: bool

    # Candidate Screening & Interviews
    selected_candidate_id: str | None
    application_id: str | None
    interview_decision: Literal["continue", "reject"] | None

    # Offer Management & Negotiation Loop
    offer_id: str | None
    base_salary: float | None
    equity: str | None
    sign_on_bonus: float | None
    start_date: str | None
    terms: str | None
    offer_decision: Literal["approved", "rejected", "negotiate"] | None
    offer_approval_request_id: str | None
    candidate_response: Literal["accepted", "negotiation", "rejected"] | None
    counter_salary: float | None
    negotiation_notes: str | None

    # Onboarding
    onboarding_task_ids: list[str]
    onboarding_completed: bool
