import logging
from typing import Any
from django.utils import timezone
from langgraph.types import Command

from orchestration.checkpointer import get_checkpointer
from orchestration.graphs.job_description import create_job_description_graph
from orchestration.graphs.recruitment import create_recruitment_graph
from workflows.models import WorkflowEvent, WorkflowExecution, WorkflowStatus

logger = logging.getLogger(__name__)


def _clean_json_val(val):
    if isinstance(val, (str, int, float, bool, type(None))):
        return val
    if isinstance(val, dict):
        return {str(k): _clean_json_val(v) for k, v in val.items() if not str(k).startswith("__")}
    if isinstance(val, (list, tuple)):
        cleaned = []
        for item in val:
            if hasattr(item, "value") or type(item).__name__ == "Interrupt":
                continue
            cleaned.append(_clean_json_val(item))
        return cleaned
    return str(val)


class WorkflowOrchestrationService:
    """Service to orchestrate LangGraph workflows, persisting execution and audit events."""

    @classmethod
    def _execute_graph(cls, workflow_graph, checkpointer, config, input_data=None):
        """Helper to run compiled graph inside checkpointer context manager or direct instance."""
        if hasattr(checkpointer, "__enter__"):
            with checkpointer as saver:
                try:
                    saver.setup()
                except Exception:
                    pass
                app = workflow_graph.compile(checkpointer=saver)
                return app.invoke(input_data, config=config)
        else:
            app = workflow_graph.compile(checkpointer=checkpointer)
            return app.invoke(input_data, config=config)

    # -----------------------------------------------------------------------
    # Phase 8: Master Recruitment Workflow Orchestration
    # -----------------------------------------------------------------------

    @classmethod
    def start_recruitment_workflow(
        cls, job, user=None, minimum_applicants: int = 1, checkpointer=None, sync: bool = True
    ) -> WorkflowExecution:
        thread_id = f"job-{job.id}-recruitment"

        execution, _ = WorkflowExecution.objects.update_or_create(
            thread_id=thread_id,
            defaults={
                "organization": job.organization,
                "job": job,
                "workflow_type": "recruitment",
                "status": WorkflowStatus.RUNNING,
                "current_step": "load_requirements",
                "error_message": "",
                "started_at": timezone.now(),
                "completed_at": None,
                "state_snapshot": {
                    "minimum_applicants": minimum_applicants,
                    "revision_count": 0,
                },
            },
        )

        WorkflowEvent.objects.create(
            execution=execution,
            event_type="recruitment_started",
            payload={"job_id": str(job.id), "title": job.title, "minimum_applicants": minimum_applicants},
        )

        initial_state = {
            "job_id": str(job.id),
            "organization_id": str(job.organization_id),
            "user_id": str(user.id) if user else None,
            "thread_id": thread_id,
            "minimum_applicants": minimum_applicants,
            "revision_count": 0,
            "published_boards": [],
            "status": "running",
            "current_step": "load_requirements",
        }

        config = {"configurable": {"thread_id": thread_id}}
        cp = checkpointer or get_checkpointer()
        graph = create_recruitment_graph()

        try:
            final_state = cls._execute_graph(graph, cp, config, input_data=initial_state)
            cls._sync_execution_state(execution, final_state)
        except Exception as e:
            logger.exception("Failed to run recruitment workflow for job %s", job.id)
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="failed",
                payload={"error": str(e)},
            )

        return execution

    @classmethod
    def resume_recruitment_workflow(
        cls, execution: WorkflowExecution, resume_data: dict[str, Any], user=None, checkpointer=None
    ) -> WorkflowExecution:
        WorkflowEvent.objects.create(
            execution=execution,
            event_type="workflow_resumed",
            payload={"resume_data": resume_data, "user_id": str(user.id) if user else None},
        )

        config = {"configurable": {"thread_id": execution.thread_id}}
        cp = checkpointer or get_checkpointer()
        graph = create_recruitment_graph()

        command = Command(resume=resume_data)

        try:
            final_state = cls._execute_graph(graph, cp, config, input_data=command)
            cls._sync_execution_state(execution, final_state)
        except Exception as e:
            logger.exception("Failed to resume recruitment workflow %s", execution.thread_id)
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="failed",
                payload={"error": str(e)},
            )

        return execution

    @classmethod
    def retry_workflow_execution(
        cls, execution: WorkflowExecution, checkpointer=None
    ) -> WorkflowExecution:
        """Retries a failed workflow execution from its last durable checkpoint."""
        execution.retry_count += 1
        execution.last_retried_at = timezone.now()
        execution.status = WorkflowStatus.RUNNING
        execution.error_message = ""
        execution.save()

        WorkflowEvent.objects.create(
            execution=execution,
            event_type="retry_initiated",
            payload={"retry_count": execution.retry_count},
        )

        config = {"configurable": {"thread_id": execution.thread_id}}
        cp = checkpointer or get_checkpointer()

        if execution.workflow_type == "recruitment":
            graph = create_recruitment_graph()
        else:
            graph = create_job_description_graph()

        try:
            # Re-invoke with None to resume from checkpoint
            final_state = cls._execute_graph(graph, cp, config, input_data=None)
            cls._sync_execution_state(execution, final_state)
        except Exception as e:
            logger.exception("Retry failed for execution %s", execution.id)
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="retry_failed",
                payload={"error": str(e)},
            )

        return execution

    @classmethod
    def _sync_execution_state(cls, execution: WorkflowExecution, state: dict[str, Any]):
        """Helper to sync LangGraph state snapshot to WorkflowExecution model."""
        clean_snapshot = {}
        has_interrupt = bool(state.get("__interrupt__"))
        interrupt_val = state.get("__interrupt__")[0].value if has_interrupt else {}

        if isinstance(state, dict):
            for k, v in state.items():
                if str(k).startswith("__"):
                    continue
                clean_snapshot[k] = _clean_json_val(v)

        execution.state_snapshot = clean_snapshot

        if state.get("error"):
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(state.get("error"))
            execution.current_step = state.get("current_step", execution.current_step)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="failed",
                payload={"error": execution.error_message},
            )
        elif has_interrupt:
            execution.status = WorkflowStatus.INTERRUPTED
            if isinstance(interrupt_val, dict) and interrupt_val.get("action") == "human_offer_approval":
                execution.current_step = "offer_approval_interrupt"
            else:
                execution.current_step = "approval_interrupt"
            clean_snapshot["current_step"] = execution.current_step
            execution.state_snapshot = clean_snapshot
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="approval_interrupted",
                payload={"step": execution.current_step, "interrupt": _clean_json_val(interrupt_val)},
            )
        elif state.get("onboarding_completed") or state.get("status") == "completed":
            execution.status = WorkflowStatus.COMPLETED
            execution.current_step = state.get("current_step", "completed")
            execution.completed_at = timezone.now()
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="recruitment_completed",
                payload={"snapshot": clean_snapshot},
            )
        else:
            execution.current_step = state.get("current_step", execution.current_step)
            execution.save()

    # -----------------------------------------------------------------------
    # Legacy / Single-purpose Job Description Workflow Orchestration
    # -----------------------------------------------------------------------

    @classmethod
    def start_job_description_workflow(
        cls, job, user=None, checkpointer=None, sync: bool = True
    ) -> WorkflowExecution:
        thread_id = f"job-{job.id}-jd"

        execution, _ = WorkflowExecution.objects.update_or_create(
            thread_id=thread_id,
            defaults={
                "organization": job.organization,
                "job": job,
                "workflow_type": "job_description",
                "status": WorkflowStatus.RUNNING,
                "current_step": "load_requirements",
                "error_message": "",
                "started_at": timezone.now(),
                "completed_at": None,
            },
        )

        WorkflowEvent.objects.create(
            execution=execution,
            event_type="generation_started",
            payload={"job_id": str(job.id), "title": job.title},
        )

        initial_state = {
            "job_id": str(job.id),
            "organization_id": str(job.organization_id),
            "user_id": str(user.id) if user else None,
            "revision_count": 0,
        }

        config = {"configurable": {"thread_id": thread_id}}
        cp = checkpointer or get_checkpointer()
        graph = create_job_description_graph()

        try:
            final_state = cls._execute_graph(graph, cp, config, input_data=initial_state)

            if final_state.get("error"):
                execution.status = WorkflowStatus.FAILED
                execution.error_message = final_state.get("error", "Unknown error")
                execution.save()
                WorkflowEvent.objects.create(
                    execution=execution,
                    event_type="failed",
                    payload={"error": execution.error_message},
                )
            else:
                execution.status = WorkflowStatus.INTERRUPTED
                execution.current_step = "approval_interrupt"
                execution.save()
                WorkflowEvent.objects.create(
                    execution=execution,
                    event_type="approval_interrupted",
                    payload={
                        "version_id": final_state.get("version_id"),
                        "version_number": final_state.get("version_number"),
                        "approval_request_id": final_state.get("approval_request_id"),
                    },
                )
        except Exception as e:
            logger.exception("Failed to run job description workflow")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="failed",
                payload={"error": str(e)},
            )

        return execution

    @classmethod
    def resume_job_description_workflow(
        cls, thread_id: str, decision: str, feedback: str = "", user=None, checkpointer=None
    ) -> WorkflowExecution | None:
        execution = WorkflowExecution.objects.filter(thread_id=thread_id).first()
        if not execution:
            import uuid
            raw_id = thread_id.replace("job-", "").replace("-jd", "")
            try:
                from jobs.models import JobRequisition
                job = JobRequisition.objects.get(id=uuid.UUID(raw_id))
                execution = WorkflowExecution.objects.create(
                    thread_id=thread_id,
                    job=job,
                    organization=job.organization,
                    status=WorkflowStatus.RUNNING,
                )
            except Exception:
                logger.warning("No WorkflowExecution found for thread_id %s", thread_id)
                return None

        WorkflowEvent.objects.create(
            execution=execution,
            event_type="resumed",
            payload={"decision": decision, "feedback": feedback, "user_id": str(user.id) if user else None},
        )

        config = {"configurable": {"thread_id": thread_id}}
        cp = checkpointer or get_checkpointer()
        graph = create_job_description_graph()

        command = Command(resume={"decision": decision, "feedback": feedback})

        try:
            final_state = cls._execute_graph(graph, cp, config, input_data=command)

            if decision == "approved":
                execution.status = WorkflowStatus.COMPLETED
                execution.current_step = "ready_for_publication"
                execution.completed_at = timezone.now()
                execution.save()
                WorkflowEvent.objects.create(
                    execution=execution,
                    event_type="approved_and_completed",
                    payload={"decision": "approved"},
                )
            elif decision == "rejected":
                execution.status = WorkflowStatus.INTERRUPTED
                execution.current_step = "approval_interrupt"
                execution.save()
                WorkflowEvent.objects.create(
                    execution=execution,
                    event_type="revision_generated",
                    payload={
                        "version_id": final_state.get("version_id"),
                        "version_number": final_state.get("version_number"),
                        "approval_request_id": final_state.get("approval_request_id"),
                    },
                )
        except Exception as e:
            logger.exception("Failed to resume workflow")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.save()
            WorkflowEvent.objects.create(
                execution=execution,
                event_type="failed",
                payload={"error": str(e)},
            )

        return execution
