import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class InterviewType(models.TextChoices):
    TECHNICAL = "technical", "Technical"
    HR = "hr", "HR"
    MANAGERIAL = "managerial", "Managerial"
    SCREENING = "screening", "Screening"
    CULTURE_FIT = "culture_fit", "Culture Fit"


class InterviewStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    RESCHEDULED = "rescheduled", "Rescheduled"


class ParticipantRole(models.TextChoices):
    LEAD = "lead", "Lead Interviewer"
    INTERVIEWER = "interviewer", "Interviewer"
    OBSERVER = "observer", "Observer"
    SCRIBE = "scribe", "Scribe"


class ParticipantStatus(models.TextChoices):
    INVITED = "invited", "Invited"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    TENTATIVE = "tentative", "Tentative"


class Recommendation(models.TextChoices):
    STRONG_HIRE = "strong_hire", "Strong Hire"
    HIRE = "hire", "Hire"
    NEUTRAL = "neutral", "Neutral / Undecided"
    NO_HIRE = "no_hire", "No Hire"
    STRONG_NO_HIRE = "strong_no_hire", "Strong No Hire"


class InterviewTemplate(models.Model):
    """
    Reusable interview guide containing default questions, duration, and rubrics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="interview_templates",
    )
    name = models.CharField(max_length=255)
    interview_type = models.CharField(
        max_length=30,
        choices=InterviewType.choices,
        default=InterviewType.TECHNICAL,
    )
    description = models.TextField(blank=True, default="")
    default_duration_minutes = models.PositiveIntegerField(default=60)
    default_questions = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_interview_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "interview_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_interview_type_display()})"


class Interview(models.Model):
    """
    Represents a scheduled or completed interview session linked to a Candidate Application.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    template = models.ForeignKey(
        InterviewTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews",
    )
    title = models.CharField(max_length=255)
    interview_type = models.CharField(
        max_length=30,
        choices=InterviewType.choices,
        default=InterviewType.TECHNICAL,
    )
    status = models.CharField(
        max_length=20,
        choices=InterviewStatus.choices,
        default=InterviewStatus.SCHEDULED,
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    location_type = models.CharField(max_length=20, default="remote")  # remote, in_person, phone
    meeting_link = models.CharField(max_length=500, blank=True, default="")
    location_details = models.CharField(max_length=255, blank=True, default="")
    prepared_questions = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_interviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_start"]
        constraints = [
            models.CheckConstraint(
                condition=Q(scheduled_end__gt=F("scheduled_start")),
                name="interview_end_after_start",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["application", "-scheduled_start"]),
            models.Index(fields=["scheduled_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.application.candidate.full_name} ({self.status})"


class InterviewParticipant(models.Model):
    """
    Panel member / interviewer assigned to an interview session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_assignments",
    )
    role = models.CharField(
        max_length=20,
        choices=ParticipantRole.choices,
        default=ParticipantRole.INTERVIEWER,
    )
    status = models.CharField(
        max_length=20,
        choices=ParticipantStatus.choices,
        default=ParticipantStatus.INVITED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["interview", "user"],
                name="unique_interview_participant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.full_name or self.user.email} in {self.interview.title} ({self.role})"


class InterviewFeedback(models.Model):
    """
    Independent feedback evaluation submitted by an interviewer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_feedbacks",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    recommendation = models.CharField(
        max_length=30,
        choices=Recommendation.choices,
        default=Recommendation.NEUTRAL,
    )
    summary = models.TextField(blank=True, default="")
    strengths = models.TextField(blank=True, default="")
    areas_for_improvement = models.TextField(blank=True, default="")
    question_scores = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["interview", "interviewer"],
                name="unique_interview_interviewer_feedback",
            )
        ]

    def __str__(self) -> str:
        return f"Feedback by {self.interviewer.email} on {self.interview.title}: {self.recommendation} ({self.rating}/5)"


class InterviewNotification(models.Model):
    """
    In-app notification and dispatch event for interview scheduling & updates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_notifications",
    )
    notification_type = models.CharField(max_length=50)  # interview_scheduled, interview_updated, cancelled, feedback_submitted
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"Notification to {self.recipient.email}: {self.title}"
