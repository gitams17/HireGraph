from typing import Literal, TypedDict


class CandidateWorkflowState(TypedDict, total=False):
    application_id: str
    candidate_id: str
    organization_id: str
    current_stage: str
    interview_decision: Literal["continue", "reject"] | None
    offer_id: str | None
    offer_status: str | None
    onboarding_tasks: list[str]
    status: str
    error: str | None
