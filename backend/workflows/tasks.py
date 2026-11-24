import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_job_description_workflow_task(self, job_id: str, user_id: str | None = None):
    """Celery task to run the JD generation workflow asynchronously."""
    from accounts.models import User
    from jobs.models import JobRequisition
    from workflows.services import WorkflowOrchestrationService

    try:
        job = JobRequisition.objects.get(id=job_id)
        user = User.objects.filter(id=user_id).first() if user_id else None
        return WorkflowOrchestrationService.start_job_description_workflow(job, user=user)
    except Exception as exc:
        logger.exception("Error executing run_job_description_workflow_task")
        raise self.retry(exc=exc, countdown=5)
