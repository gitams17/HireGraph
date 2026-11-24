from typing import Any, TypedDict


class HiringGraphState(TypedDict, total=False):
    job_id: str
    organization_id: str
    user_id: str
    requirements: dict[str, Any]
    generated_jd: dict[str, Any]
    raw_markdown: str
    version_id: str
    version_number: int
    approval_request_id: str
    feedback: str | None
    decision: str | None  # "approved" | "rejected"
    status: str
    revision_count: int
    error: str | None
