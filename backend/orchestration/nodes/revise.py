from typing import Any
from orchestration.state.hiring import HiringGraphState


def capture_feedback_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Record rejection feedback on the JD version."""
    version_id = state.get("version_id")
    feedback = state.get("feedback", "")

    from jobs.models import JobDescriptionVersion
    if version_id:
        JobDescriptionVersion.objects.filter(id=version_id).update(status="rejected")

    return {
        "feedback": feedback,
        "status": "feedback_captured",
    }


def generate_revision_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Prepares revision input for the next generation cycle."""
    requirements = dict(state.get("requirements", {}))
    requirements["previous_jd"] = state.get("raw_markdown", "")

    revision_count = state.get("revision_count", 0) + 1

    return {
        "requirements": requirements,
        "revision_count": revision_count,
        "status": "revision_prepared",
    }
