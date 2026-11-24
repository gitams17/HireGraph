from typing import Any, TypedDict


class ResumeScreeningState(TypedDict, total=False):
    application_id: str
    resume_id: str
    job_id: str
    user_id: str | None
    job_requirements: dict[str, Any]
    file_path: str
    filename: str
    raw_text: str
    cleaned_text: str
    is_scanned: bool
    injection_detected: bool
    extracted_data: dict[str, Any]
    assessment: dict[str, Any]
    ats_score: int
    analysis_id: str
    status: str  # "pending" | "processing" | "completed" | "failed"
    error: str | None
