import logging
import uuid
from typing import Any, Protocol

from workflows.models import JobPublication, JobPublicationStatus

logger = logging.getLogger(__name__)


class BaseJobBoardAdapter(Protocol):
    def publish(self, job, payload: dict[str, Any] | None = None) -> JobPublication:
        ...


class MockJobBoardAdapter:
    """Mock Job Board Adapter for tests and local development."""

    def __init__(self, board_name: str = "mock_board", should_fail: bool = False):
        self.board_name = board_name
        self.should_fail = should_fail

    def publish(self, job, payload: dict[str, Any] | None = None) -> JobPublication:
        if self.should_fail:
            pub, _ = JobPublication.objects.update_or_create(
                job=job,
                board_name=self.board_name,
                defaults={
                    "status": JobPublicationStatus.FAILED,
                    "payload": payload or {"error": "Simulated external job board connection failure"},
                },
            )
            raise RuntimeError(f"External job board {self.board_name} returned 503 Service Unavailable.")

        ext_id = f"{self.board_name[:3].lower()}-{uuid.uuid4().hex[:8]}"
        posting_url = f"https://jobs.{self.board_name}.example.com/postings/{ext_id}"

        from django.utils import timezone
        pub, _ = JobPublication.objects.update_or_create(
            job=job,
            board_name=self.board_name,
            defaults={
                "external_id": ext_id,
                "status": JobPublicationStatus.PUBLISHED,
                "posting_url": posting_url,
                "payload": payload or {"title": job.title, "department": job.department},
                "published_at": timezone.now(),
            },
        )
        return pub


class LinkedInJobBoardAdapter(MockJobBoardAdapter):
    def __init__(self, should_fail: bool = False):
        super().__init__(board_name="linkedin", should_fail=should_fail)


class IndeedJobBoardAdapter(MockJobBoardAdapter):
    def __init__(self, should_fail: bool = False):
        super().__init__(board_name="indeed", should_fail=should_fail)


def get_job_board_adapter(board_name: str = "mock_board", should_fail: bool = False) -> BaseJobBoardAdapter:
    b = board_name.lower().strip()
    if b == "linkedin":
        return LinkedInJobBoardAdapter(should_fail=should_fail)
    elif b == "indeed":
        return IndeedJobBoardAdapter(should_fail=should_fail)
    return MockJobBoardAdapter(board_name=b, should_fail=should_fail)
