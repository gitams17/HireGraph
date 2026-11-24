import logging
from applications.models import Application
from interviews.models import Interview, InterviewFeedback
from orchestration.state.recruitment import RecruitmentWorkflowState

logger = logging.getLogger(__name__)


def evaluate_interview_decision_node(state: RecruitmentWorkflowState) -> dict:
    """
    Synthesizes panel feedback across interviews for the active candidate application.
    Decides whether to advance candidate to offer preparation or reject.
    """
    app_id = state.get("application_id")
    if not app_id:
        # Check if an application exists for this job
        job_id = state.get("job_id")
        app = Application.objects.filter(job_id=job_id).first()
        if app:
            app_id = str(app.id)

    if not app_id:
        return {
            "status": "running",
            "current_step": "evaluate_interview_decision",
            "interview_decision": "continue",  # Default if mock run
        }

    feedbacks = InterviewFeedback.objects.filter(interview__application_id=app_id)
    if not feedbacks.exists():
        # Fallback or simulated decision
        decision = state.get("interview_decision") or "continue"
        return {
            "application_id": app_id,
            "current_step": "evaluate_interview_decision",
            "interview_decision": decision,
        }

    # Calculate average rating and check recommendations
    avg_rating = sum(f.rating for f in feedbacks) / feedbacks.count()
    has_strong_no_hire = any(f.recommendation == "strong_no_hire" for f in feedbacks)

    decision = "reject" if (has_strong_no_hire or avg_rating < 3.0) else "continue"

    return {
        "application_id": app_id,
        "current_step": "evaluate_interview_decision",
        "interview_decision": decision,
    }
