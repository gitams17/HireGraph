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


@shared_task(bind=True, max_retries=2)
def run_resume_screening_task(self, application_id: str, user_id: str | None = None):
    """Celery task to execute the LangGraph Resume Screening workflow."""
    from orchestration.graphs.resume_screening import get_resume_screening_app

    try:
        app_graph = get_resume_screening_app()
        initial_state = {
            "application_id": str(application_id),
            "user_id": str(user_id) if user_id else None,
            "status": "pending",
        }
        result = app_graph.invoke(initial_state)
        return result
    except Exception as exc:
        logger.exception("Error executing run_resume_screening_task for application %s", application_id)
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3)
def run_recruitment_workflow_task(
    self, job_id: str, user_id: str | None = None, minimum_applicants: int = 1
):
    """
    Celery task to execute the Master Recruitment Workflow (Phase 8).
    Coordinates JD generation, external publication, applicant volume monitoring,
    screening, interview evaluation, offers, and onboarding.
    """
    from accounts.models import User
    from jobs.models import JobRequisition
    from workflows.services import WorkflowOrchestrationService

    try:
        job = JobRequisition.objects.get(id=job_id)
        user = User.objects.filter(id=user_id).first() if user_id else None
        return WorkflowOrchestrationService.start_recruitment_workflow(
            job=job, user=user, minimum_applicants=minimum_applicants
        )
    except Exception as exc:
        logger.exception("Error executing run_recruitment_workflow_task for job %s", job_id)
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=2)
def monitor_applicant_volume_periodic_task(self):
    """
    Celery Beat periodic task:
    Periodically checks open job requisitions associated with active recruitment workflows.
    If applicant count is below minimum threshold, logs warnings or alerts recruiters.
    """
    from applications.models import Application
    from jobs.models import JobRequisition, JobStatus
    from workflows.models import WorkflowExecution, WorkflowStatus

    logger.info("Executing Celery Beat: monitor_applicant_volume_periodic_task")

    open_jobs = JobRequisition.objects.filter(status=JobStatus.OPEN)
    results = []

    for job in open_jobs:
        count = Application.objects.filter(job=job).count()
        execution = WorkflowExecution.objects.filter(
            job=job,
            workflow_type="recruitment",
            status=WorkflowStatus.RUNNING,
        ).first()

        threshold = 1
        if execution and isinstance(execution.state_snapshot, dict):
            threshold = execution.state_snapshot.get("minimum_applicants", 1)

        is_sufficient = count >= threshold
        results.append(
            {
                "job_id": str(job.id),
                "title": job.title,
                "applicants": count,
                "threshold": threshold,
                "sufficient": is_sufficient,
            }
        )

    logger.info("Application volume monitoring completed for %d jobs: %s", len(open_jobs), results)
    return results


@shared_task(bind=True, max_retries=2)
def resume_recruitment_workflow_task(self, execution_id: str, resume_data: dict, user_id: str | None = None):
    """Celery task to resume an interrupted recruitment workflow with human input."""
    from accounts.models import User
    from workflows.models import WorkflowExecution
    from workflows.services import WorkflowOrchestrationService

    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        user = User.objects.filter(id=user_id).first() if user_id else None
        return WorkflowOrchestrationService.resume_recruitment_workflow(
            execution=execution, resume_data=resume_data, user=user
        )
    except Exception as exc:
        logger.exception("Error executing resume_recruitment_workflow_task for execution %s", execution_id)
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=2)
def retry_workflow_execution_task(self, execution_id: str):
    """Celery task to retry a failed workflow execution from its last checkpoint."""
    from workflows.models import WorkflowExecution
    from workflows.services import WorkflowOrchestrationService

    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        return WorkflowOrchestrationService.retry_workflow_execution(execution)
    except Exception as exc:
        logger.exception("Error executing retry_workflow_execution_task for execution %s", execution_id)
        raise self.retry(exc=exc, countdown=5)
