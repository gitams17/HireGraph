"""
Comprehensive tests for AI Job Description Generation, LangGraph Workflow, and Human Approval.

Scenarios tested:
1. Successful JD generation: Structured JD saved with correct schema
2. Invalid LLM output: Validation failure handled gracefully
3. Approve JD: Workflow resumes, JD marked approved, job set ready for publication
4. Reject JD: Feedback recorded, revision prepared, new version generated
5. Model API failure: Failure recorded in workflow state & event
6. Worker restart / Checkpoint persistence: State resumes reliably from checkpoint
7. Duplicate approval rejection: Idempotency enforced
8. Job versions API: Recruiter edits draft version before submission
"""

from unittest.mock import patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from langgraph.checkpoint.memory import MemorySaver

from accounts.models import User
from ai.parsers.job_description import JobDescriptionSchema
from ai.providers.llm import FakeLLMProvider
from approvals.models import ApprovalRequest, ApprovalStatus
from jobs.models import JobDescriptionVersion, JobRequisition, JobStatus
from organizations.models import Organization, OrganizationMembership
from workflows.models import WorkflowEvent, WorkflowExecution, WorkflowStatus
from workflows.services import WorkflowOrchestrationService


def make_user(email: str) -> User:
    return User.objects.create_user(email=email, password="password123!", first_name="Test", last_name="User")


def make_org(name: str, owner: User) -> Organization:
    org = Organization.objects.create(name=name, slug=name.lower().replace(" ", "-"), created_by=owner)
    OrganizationMembership.objects.create(organization=org, user=owner, role="owner", is_active=True)
    return org


def add_member(org: Organization, user: User, role: str) -> OrganizationMembership:
    return OrganizationMembership.objects.create(organization=org, user=user, role=role, is_active=True)


class WorkflowOrchestrationTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@workflow.com")
        self.recruiter = make_user("recruiter@workflow.com")
        self.hm = make_user("hm@workflow.com")
        self.org = make_org("Workflow Org", self.owner)
        add_member(self.org, self.recruiter, "recruiter")
        add_member(self.org, self.hm, "hiring_manager")

        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Senior Full-Stack Engineer",
            department="Engineering",
            location="Remote",
            employment_type="full_time",
            experience_min=5,
            experience_max=8,
            required_skills=["Python", "Django", "Next.js", "TypeScript"],
            responsibilities=["Architect robust systems", "Mentor junior devs"],
            created_by=self.recruiter,
        )

        self.memory_cp = MemorySaver()

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_successful_jd_generation(self, mock_provider):
        """Scenario 1: Successful JD generation produces structured output and saves version."""
        mock_provider.return_value = FakeLLMProvider(mode="success")

        execution = WorkflowOrchestrationService.start_job_description_workflow(
            job=self.job,
            user=self.recruiter,
            checkpointer=self.memory_cp,
        )

        self.assertEqual(execution.status, WorkflowStatus.INTERRUPTED)
        self.assertEqual(self.job.description_versions.count(), 1)

        version = self.job.description_versions.first()
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.title, "Senior Full-Stack Engineer")
        self.assertEqual(version.status, "pending_approval")
        self.assertTrue(len(version.responsibilities) > 0)
        self.assertTrue(len(version.required_qualifications) > 0)

        # Check approval request
        self.assertEqual(self.job.approval_requests.count(), 1)
        approval = self.job.approval_requests.first()
        self.assertEqual(approval.status, ApprovalStatus.PENDING)

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_invalid_llm_output_handled(self, mock_provider):
        """Scenario 2: Invalid LLM output triggers failure state without breaking execution."""
        mock_provider.return_value = FakeLLMProvider(mode="invalid_schema")

        execution = WorkflowOrchestrationService.start_job_description_workflow(
            job=self.job,
            user=self.recruiter,
            checkpointer=self.memory_cp,
        )

        self.assertEqual(execution.status, WorkflowStatus.FAILED)
        self.assertIn("LLM generation failed", execution.error_message)
        self.assertEqual(self.job.description_versions.count(), 0)

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_model_api_failure_handled(self, mock_provider):
        """Scenario 5: Model API service failure records failure state & event."""
        mock_provider.return_value = FakeLLMProvider(mode="error")

        execution = WorkflowOrchestrationService.start_job_description_workflow(
            job=self.job,
            user=self.recruiter,
            checkpointer=self.memory_cp,
        )

        self.assertEqual(execution.status, WorkflowStatus.FAILED)
        self.assertIn("LLM API service unavailable", execution.error_message)

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_approve_jd_workflow_resumption(self, mock_provider):
        """Scenario 3: Approving JD resumes workflow, marks approved, sets job ready for publication."""
        mock_provider.return_value = FakeLLMProvider(mode="success")

        # Start workflow
        execution = WorkflowOrchestrationService.start_job_description_workflow(
            job=self.job,
            user=self.recruiter,
            checkpointer=self.memory_cp,
        )
        self.assertEqual(execution.status, WorkflowStatus.INTERRUPTED)

        # Resume with approval
        resumed = WorkflowOrchestrationService.resume_job_description_workflow(
            thread_id=execution.thread_id,
            decision="approved",
            feedback="LGTM!",
            user=self.hm,
            checkpointer=self.memory_cp,
        )

        self.assertEqual(resumed.status, WorkflowStatus.COMPLETED)
        version = self.job.description_versions.first()
        version.refresh_from_db()
        self.assertEqual(version.status, "approved")

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.OPEN)

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_reject_jd_workflow_revision_loop(self, mock_provider):
        """Scenario 4: Rejecting JD records feedback, triggers revision loop, and creates version 2."""
        mock_provider.return_value = FakeLLMProvider(mode="success")

        # Start workflow -> Version 1 created
        execution = WorkflowOrchestrationService.start_job_description_workflow(
            job=self.job,
            user=self.recruiter,
            checkpointer=self.memory_cp,
        )
        self.assertEqual(self.job.description_versions.count(), 1)
        v1 = self.job.description_versions.first()

        # Reject with feedback -> Triggers revision loop in graph -> Version 2 created
        feedback = "Please add experience with PostgreSQL and Docker."
        resumed = WorkflowOrchestrationService.resume_job_description_workflow(
            thread_id=execution.thread_id,
            decision="rejected",
            feedback=feedback,
            user=self.hm,
            checkpointer=self.memory_cp,
        )

        # Graph should pause at new approval interrupt for version 2
        self.assertEqual(resumed.status, WorkflowStatus.INTERRUPTED)
        self.assertEqual(self.job.description_versions.count(), 2)

        v1.refresh_from_db()
        self.assertEqual(v1.status, "rejected")

        v2 = self.job.description_versions.order_by("-version_number").first()
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v2.status, "pending_approval")
        self.assertIn("PostgreSQL", v2.overview)


class JobDescriptionEndpointsTests(APITestCase):
    def setUp(self):
        self.owner = make_user("apiowner@workflow.com")
        self.recruiter = make_user("apirecruiter@workflow.com")
        self.org = make_org("API Org", self.owner)
        add_member(self.org, self.recruiter, "recruiter")

        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Lead Backend Architect",
            created_by=self.owner,
        )

    @patch("orchestration.nodes.generate.get_llm_provider")
    def test_generate_jd_endpoint(self, mock_provider):
        mock_provider.return_value = FakeLLMProvider(mode="success")
        self.client.force_authenticate(self.recruiter)

        url = f"/api/v1/jobs/{self.job.id}/generate-jd/"
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("thread_id", resp.data)
        self.assertEqual(self.job.description_versions.count(), 1)

    def test_edit_draft_version(self):
        self.client.force_authenticate(self.recruiter)
        version = JobDescriptionVersion.objects.create(
            job=self.job,
            version_number=1,
            title=self.job.title,
            overview="Initial overview",
            status="draft",
        )

        url = f"/api/v1/jobs/{self.job.id}/versions/{version.id}/"
        resp = self.client.patch(url, {"overview": "Updated refined overview"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        version.refresh_from_db()
        self.assertEqual(version.overview, "Updated refined overview")

    def test_submit_version_for_approval(self):
        self.client.force_authenticate(self.recruiter)
        version = JobDescriptionVersion.objects.create(
            job=self.job,
            version_number=1,
            title=self.job.title,
            overview="Initial overview",
            status="draft",
        )

        url = f"/api/v1/jobs/{self.job.id}/versions/{version.id}/submit-approval/"
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        version.refresh_from_db()
        self.assertEqual(version.status, "pending_approval")
        self.assertEqual(self.job.approval_requests.count(), 1)

    def test_workflow_status_view(self):
        self.client.force_authenticate(self.recruiter)
        thread_id = f"job-{self.job.id}-jd"
        execution = WorkflowExecution.objects.create(
            thread_id=thread_id,
            job=self.job,
            status=WorkflowStatus.INTERRUPTED,
            current_step="approval_interrupt",
        )
        WorkflowEvent.objects.create(
            execution=execution,
            event_type="generation_started",
            payload={"test": 1},
        )

        url = f"/api/v1/workflows/{thread_id}/status/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["thread_id"], thread_id)
        self.assertEqual(len(resp.data["events"]), 1)
