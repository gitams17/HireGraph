import logging
from typing import Any
from django.utils import timezone
from langgraph.types import Command

from orchestration.graphs.job_description import create_job_description_graph, get_checkpointer
from workflows.models import WorkflowEvent, WorkflowExecution, WorkflowStatus

logger = logging.getLogger(__name__)


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

    @classmethod
    def start_job_description_workflow(
        cls, job, user=None, checkpointer=None, sync: bool = True
    ) -> WorkflowExecution:
        thread_id = f"job-{job.id}-jd"

        execution, _ = WorkflowExecution.objects.update_or_create(
            thread_id=thread_id,
            defaults={
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
                # Graph paused at interrupt
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
                # A revision was prepared and new JD generated, then halted at next interrupt
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
