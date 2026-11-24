import datetime
import logging
from langgraph.types import interrupt

from applications.models import Application, ApplicationEvent, ApplicationStage
from orchestration.state.recruitment import RecruitmentWorkflowState
from workflows.models import (
    Offer,
    OfferStatus,
    OnboardingTask,
    OnboardingTaskCategory,
    OnboardingTaskStatus,
)

logger = logging.getLogger(__name__)


def prepare_offer_node(state: RecruitmentWorkflowState) -> dict:
    """Prepares an official offer record for the selected candidate."""
    app_id = state.get("application_id")
    job_id = state.get("job_id")

    app = None
    if app_id:
        app = Application.objects.select_related("organization", "candidate", "job").filter(id=app_id).first()
    elif job_id:
        app = Application.objects.select_related("organization", "candidate", "job").filter(job_id=job_id).first()

    if not app:
        return {
            "status": "failed",
            "error": "No candidate application found for offer preparation.",
        }

    salary = state.get("base_salary") or 140000.00
    equity = state.get("equity") or "0.15% Equity"
    start_date = state.get("start_date") or (datetime.date.today() + datetime.timedelta(days=30)).isoformat()

    offer, _ = Offer.objects.update_or_create(
        application=app,
        organization=app.organization,
        defaults={
            "base_salary": salary,
            "equity": equity,
            "start_date": start_date,
            "status": OfferStatus.PENDING_APPROVAL,
            "terms": "Standard full-time employment agreement with healthcare & 401k.",
        },
    )

    return {
        "status": "running",
        "current_step": "prepare_offer",
        "application_id": str(app.id),
        "offer_id": str(offer.id),
        "base_salary": float(offer.base_salary),
        "equity": offer.equity,
        "start_date": str(offer.start_date),
    }


def offer_approval_interrupt_node(state: RecruitmentWorkflowState) -> dict:
    """Pauses graph execution to await human offer approval or negotiation terms."""
    offer_id = state.get("offer_id")
    human_input = interrupt(
        {
            "action": "human_offer_approval",
            "offer_id": offer_id,
            "base_salary": state.get("base_salary"),
            "equity": state.get("equity"),
            "prompt": "Please review and approve the candidate offer compensation and terms.",
        }
    )

    if isinstance(human_input, dict):
        res = {
            "offer_decision": human_input.get("decision", "approved"),
            "feedback": human_input.get("feedback", ""),
            "base_salary": human_input.get("base_salary", state.get("base_salary")),
        }
        if "candidate_response" in human_input:
            res["candidate_response"] = human_input["candidate_response"]
        if "counter_salary" in human_input:
            res["counter_salary"] = human_input["counter_salary"]
        if "negotiation_notes" in human_input:
            res["negotiation_notes"] = human_input["negotiation_notes"]
        return res
    return {"offer_decision": "approved"}


def send_offer_node(state: RecruitmentWorkflowState) -> dict:
    """Dispatches the approved offer to the candidate."""
    offer_id = state.get("offer_id")
    if offer_id:
        Offer.objects.filter(id=offer_id).update(status=OfferStatus.SENT)

    app_id = state.get("application_id")
    if app_id:
        Application.objects.filter(id=app_id).update(stage=ApplicationStage.INTERVIEW)  # or offer stage
        ApplicationEvent.objects.create(
            application_id=app_id,
            event_type="offer_sent",
            notes=f"Offer sent to candidate with base salary {state.get('base_salary')}.",
        )

    # Simulated or injected candidate response (default: accepted)
    cand_resp = state.get("candidate_response") or "accepted"

    return {
        "status": "running",
        "current_step": "send_offer",
        "candidate_response": cand_resp,
    }


def revise_offer_node(state: RecruitmentWorkflowState) -> dict:
    """Adjusts offer parameters in response to candidate counter-proposals/negotiation."""
    offer_id = state.get("offer_id")
    counter_salary = state.get("counter_salary") or (float(state.get("base_salary", 140000)) + 10000.0)
    notes = state.get("negotiation_notes") or "Candidate requested salary adjustment based on competing offer."

    if offer_id:
        Offer.objects.filter(id=offer_id).update(
            status=OfferStatus.NEGOTIATING,
            counter_salary=counter_salary,
            negotiation_notes=notes,
        )

    return {
        "status": "running",
        "current_step": "revise_offer",
        "base_salary": counter_salary,
        "negotiation_notes": notes,
        "candidate_response": None,  # Reset for next round
    }


def close_application_node(state: RecruitmentWorkflowState) -> dict:
    """Closes and rejects an application when interview or offer negotiation fails."""
    app_id = state.get("application_id")
    if app_id:
        Application.objects.filter(id=app_id).update(
            stage=ApplicationStage.REJECTED,
            rejection_reason="Candidate not selected following interview review or offer withdrawal.",
        )
        ApplicationEvent.objects.create(
            application_id=app_id,
            event_type="stage_changed",
            to_stage=ApplicationStage.REJECTED,
            notes="Application closed.",
        )
    return {
        "status": "completed",
        "current_step": "close_application",
    }


def initiate_onboarding_node(state: RecruitmentWorkflowState) -> dict:
    """Initializes standard onboarding workflow tasks upon offer acceptance."""
    app_id = state.get("application_id")
    app = None
    if app_id:
        app = Application.objects.select_related("organization", "candidate").filter(id=app_id).first()

    if not app:
        return {"status": "completed", "onboarding_completed": True}

    # Mark application selected / hired
    app.stage = ApplicationStage.SELECTED
    app.save(update_fields=["stage", "updated_at"])

    Offer.objects.filter(application=app).update(status=OfferStatus.ACCEPTED)

    tasks_to_create = [
        ("Sign Employment Agreement & NDAs", OnboardingTaskCategory.COMPLIANCE, 3),
        ("Background & Reference Check Verification", OnboardingTaskCategory.COMPLIANCE, 5),
        ("Hardware & Engineering Laptop Provisioning", OnboardingTaskCategory.IT_SETUP, 7),
        ("Set Up Corporate Email, GitHub & Slack", OnboardingTaskCategory.IT_SETUP, 7),
        ("HR Benefits & Direct Deposit Paperwork", OnboardingTaskCategory.HR_PAPERWORK, 10),
        ("Welcome Session & Team Architecture Briefing", OnboardingTaskCategory.TEAM_INTRO, 14),
    ]

    created_ids = []
    today = datetime.date.today()
    for title, cat, days in tasks_to_create:
        task = OnboardingTask.objects.create(
            organization=app.organization,
            application=app,
            title=title,
            category=cat,
            status=OnboardingTaskStatus.PENDING,
            due_date=today + datetime.timedelta(days=days),
        )
        created_ids.append(str(task.id))

    ApplicationEvent.objects.create(
        application=app,
        event_type="onboarding_initiated",
        notes=f"Offer accepted. Created {len(created_ids)} onboarding tasks.",
    )

    return {
        "status": "completed",
        "current_step": "initiate_onboarding",
        "onboarding_task_ids": created_ids,
        "onboarding_completed": True,
    }
