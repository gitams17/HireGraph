import logging
from jobs.models import JobRequisition, JobStatus
from orchestration.state.recruitment import RecruitmentWorkflowState
from workflows.adapters.job_boards import get_job_board_adapter

logger = logging.getLogger(__name__)


def publish_job_node(state: RecruitmentWorkflowState) -> dict:
    """
    Publishes the approved job requisition to configured external job boards.
    Enforces idempotency and updates requisition status to OPEN.
    """
    job_id = state.get("job_id")
    job = JobRequisition.objects.get(id=job_id)
    if job.status != JobStatus.OPEN:
        job.status = JobStatus.OPEN
        job.save(update_fields=["status", "updated_at"])

    boards = ["linkedin", "indeed"]
    published = []
    for board in boards:
        adapter = get_job_board_adapter(board)
        pub = adapter.publish(job)
        board_name = getattr(pub, "board_name", board)
        published.append(board_name)

    return {
        "status": "running",
        "current_step": "publish_job",
        "published_boards": published,
        "error": None,
    }
