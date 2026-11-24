from typing import Any
from langgraph.types import interrupt

from orchestration.state.hiring import HiringGraphState


def save_version_node(state: HiringGraphState) -> dict[str, Any]:
    """
    Node: Save the generated JobDescriptionVersion to the database
    and create or associate an ApprovalRequest.
    """
    if state.get("status") == "failed" or not state.get("generated_jd"):
        return {"status": "failed"}

    job_id = state.get("job_id")
    user_id = state.get("user_id")
    generated_jd = state.get("generated_jd", {})
    raw_markdown = state.get("raw_markdown", "")

    from accounts.models import User
    from approvals.models import ApprovalRequest
    from jobs.models import JobDescriptionVersion, JobRequisition

    try:
        job = JobRequisition.objects.get(id=job_id)
        user = User.objects.filter(id=user_id).first() if user_id else None

        # Next version number
        last_version = job.description_versions.order_by("-version_number").first()
        version_number = (last_version.version_number + 1) if last_version else 1

        version = JobDescriptionVersion.objects.create(
            job=job,
            version_number=version_number,
            title=generated_jd.get("title", job.title),
            overview=generated_jd.get("overview", ""),
            responsibilities=generated_jd.get("responsibilities", []),
            required_qualifications=generated_jd.get("required_qualifications", []),
            preferred_qualifications=generated_jd.get("preferred_qualifications", []),
            benefits=generated_jd.get("benefits", []),
            raw_content=raw_markdown,
            status="pending_approval",
            created_by=user,
        )

        approval_request = ApprovalRequest.objects.create(
            organization=job.organization,
            job=job,
            version=version,
            requested_by=user or job.created_by,
            status="pending",
        )

        return {
            "version_id": str(version.id),
            "version_number": version_number,
            "approval_request_id": str(approval_request.id),
            "status": "pending_approval",
        }
    except Exception as e:
        return {"error": f"Failed to save JD version: {e}", "status": "failed"}


def approval_interrupt_node(state: HiringGraphState) -> dict[str, Any]:
    """
    Node: Suspends execution using LangGraph interrupt.
    Resumed by human decision ("approved" or "rejected").
    """
    if state.get("status") == "failed":
        return state

    decision_data = interrupt({
        "message": "Human approval required for Job Description",
        "job_id": state.get("job_id"),
        "version_id": state.get("version_id"),
        "version_number": state.get("version_number"),
        "approval_request_id": state.get("approval_request_id"),
    })

    # When resumed, decision_data is returned from Command(resume=...)
    decision = decision_data.get("decision") if isinstance(decision_data, dict) else str(decision_data)
    feedback = decision_data.get("feedback") if isinstance(decision_data, dict) else None

    return {
        "decision": decision,
        "feedback": feedback,
        "status": f"decision_{decision}",
    }


def mark_approved_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Mark JD version as approved and update JobRequisition."""
    version_id = state.get("version_id")
    job_id = state.get("job_id")

    from jobs.models import JobDescriptionVersion, JobRequisition

    try:
        if version_id:
            JobDescriptionVersion.objects.filter(id=version_id).update(status="approved")
        return {"status": "approved"}
    except Exception as e:
        return {"error": f"Failed to mark version approved: {e}", "status": "failed"}


def ready_for_publication_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Mark JobRequisition as open / ready for publication."""
    job_id = state.get("job_id")
    from jobs.models import JobRequisition, JobStatus

    try:
        JobRequisition.objects.filter(id=job_id).update(status=JobStatus.OPEN)
        return {"status": "ready_for_publication"}
    except Exception as e:
        return {"error": f"Failed to update job status: {e}", "status": "failed"}
