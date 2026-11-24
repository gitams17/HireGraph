"""
Master Recruitment Workflow Graph (Phase 8: Advanced Workflow Automation).
Orchestrates the entire hiring lifecycle from requisition and JD generation,
through approval, job publication, applicant volume monitoring, resume screening,
interview feedback synthesis, offer negotiation loops, and onboarding.
"""

from typing import Literal
from langgraph.graph import END, StateGraph

from orchestration.checkpointer import get_checkpointer
from orchestration.nodes.approve import (
    approval_interrupt_node,
    mark_approved_node,
    save_version_node,
)
from orchestration.nodes.generate import generate_jd_node, load_requirements_node
from orchestration.nodes.manage_offer import (
    close_application_node,
    initiate_onboarding_node,
    offer_approval_interrupt_node,
    prepare_offer_node,
    revise_offer_node,
    send_offer_node,
)
from orchestration.nodes.publish_job import publish_job_node
from orchestration.nodes.revise import capture_feedback_node, generate_revision_node
from orchestration.nodes.schedule_interview import evaluate_interview_decision_node
from orchestration.state.recruitment import RecruitmentWorkflowState


# ---------------------------------------------------------------------------
# Applicant Monitoring Node
# ---------------------------------------------------------------------------

def monitor_applicants_node(state: RecruitmentWorkflowState) -> dict:
    """Evaluates applicant count against minimum volume threshold."""
    from applications.models import Application

    job_id = state.get("job_id")
    min_apps = state.get("minimum_applicants", 1)

    app_count = Application.objects.filter(job_id=job_id).count()
    first_app = Application.objects.filter(job_id=job_id).first()

    passed = app_count >= min_apps

    return {
        "status": "running",
        "current_step": "monitor_applicants",
        "applicant_count": app_count,
        "applicant_monitoring_passed": passed,
        "application_id": str(first_app.id) if first_app else state.get("application_id"),
    }


def notify_recruiter_node(state: RecruitmentWorkflowState) -> dict:
    """Notifies recruiter that applicant volume is low, triggering JD revision request."""
    return {
        "status": "running",
        "current_step": "notify_recruiter",
        "feedback": "Applicant volume is below threshold. Please review and revise job description requirements or distribution.",
    }


def screen_candidates_node(state: RecruitmentWorkflowState) -> dict:
    """Runs candidate resume screening."""
    return {
        "status": "running",
        "current_step": "screen_candidates",
    }


# ---------------------------------------------------------------------------
# Routing Functions
# ---------------------------------------------------------------------------

def route_after_jd_approval(state: RecruitmentWorkflowState) -> Literal["mark_approved", "capture_feedback", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    decision = state.get("decision")
    if decision == "approved":
        return "mark_approved"
    elif decision == "rejected":
        return "capture_feedback"
    return END


def route_after_applicant_monitoring(state: RecruitmentWorkflowState) -> Literal["screen_candidates", "notify_recruiter", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    if state.get("applicant_monitoring_passed"):
        return "screen_candidates"
    return "notify_recruiter"


def route_after_interview_decision(state: RecruitmentWorkflowState) -> Literal["prepare_offer", "close_application", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    decision = state.get("interview_decision")
    if decision == "continue":
        return "prepare_offer"
    return "close_application"


def route_after_offer_approval(state: RecruitmentWorkflowState) -> Literal["send_offer", "close_application", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    decision = state.get("offer_decision")
    if decision == "approved":
        return "send_offer"
    return "close_application"


def route_after_candidate_response(state: RecruitmentWorkflowState) -> Literal["initiate_onboarding", "revise_offer", "close_application", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    resp = state.get("candidate_response")
    if resp == "accepted":
        return "initiate_onboarding"
    elif resp == "negotiation":
        return "revise_offer"
    return "close_application"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def create_recruitment_graph():
    """Builds and returns the uncompiled master recruitment StateGraph."""
    workflow = StateGraph(RecruitmentWorkflowState)

    # 1. JD Generation & Approval Nodes
    workflow.add_node("load_requirements", load_requirements_node)
    workflow.add_node("generate_jd", generate_jd_node)
    workflow.add_node("save_version", save_version_node)
    workflow.add_node("approval_interrupt", approval_interrupt_node)
    workflow.add_node("mark_approved", mark_approved_node)
    workflow.add_node("capture_feedback", capture_feedback_node)
    workflow.add_node("generate_revision", generate_revision_node)

    # 2. Publication & Applicant Volume Monitoring Nodes
    workflow.add_node("publish_job", publish_job_node)
    workflow.add_node("monitor_applicants", monitor_applicants_node)
    workflow.add_node("notify_recruiter", notify_recruiter_node)

    # 3. Candidate Screening & Interview Nodes
    workflow.add_node("screen_candidates", screen_candidates_node)
    workflow.add_node("evaluate_interview_decision", evaluate_interview_decision_node)

    # 4. Offer Management & Negotiation Loop Nodes
    workflow.add_node("prepare_offer", prepare_offer_node)
    workflow.add_node("offer_approval_interrupt", offer_approval_interrupt_node)
    workflow.add_node("send_offer", send_offer_node)
    workflow.add_node("revise_offer", revise_offer_node)
    workflow.add_node("close_application", close_application_node)

    # 5. Onboarding Node
    workflow.add_node("initiate_onboarding", initiate_onboarding_node)

    # --- EDGES ---
    # Entry & JD Generation
    workflow.set_entry_point("load_requirements")
    workflow.add_edge("load_requirements", "generate_jd")
    workflow.add_edge("generate_jd", "save_version")
    workflow.add_edge("save_version", "approval_interrupt")

    # JD Approval Routing
    workflow.add_conditional_edges(
        "approval_interrupt",
        route_after_jd_approval,
        {
            "mark_approved": "mark_approved",
            "capture_feedback": "capture_feedback",
            END: END,
        },
    )

    # Revision loop
    workflow.add_edge("capture_feedback", "generate_revision")
    workflow.add_edge("generate_revision", "generate_jd")

    # Approved -> Publication -> Application Monitoring
    workflow.add_edge("mark_approved", "publish_job")
    workflow.add_edge("publish_job", "monitor_applicants")

    # Enough applicants conditional router
    workflow.add_conditional_edges(
        "monitor_applicants",
        route_after_applicant_monitoring,
        {
            "screen_candidates": "screen_candidates",
            "notify_recruiter": "notify_recruiter",
            END: END,
        },
    )

    # Insufficient applicants: notify recruiter -> revise JD
    workflow.add_edge("notify_recruiter", "capture_feedback")

    # Screening -> Interview Evaluation
    workflow.add_edge("screen_candidates", "evaluate_interview_decision")

    # Interview Decision conditional router
    workflow.add_conditional_edges(
        "evaluate_interview_decision",
        route_after_interview_decision,
        {
            "prepare_offer": "prepare_offer",
            "close_application": "close_application",
            END: END,
        },
    )

    # Offer Preparation -> Offer Approval Interrupt
    workflow.add_edge("prepare_offer", "offer_approval_interrupt")

    # Offer Approval Interrupt conditional router
    workflow.add_conditional_edges(
        "offer_approval_interrupt",
        route_after_offer_approval,
        {
            "send_offer": "send_offer",
            "close_application": "close_application",
            END: END,
        },
    )

    # Send Offer -> Candidate Response conditional router
    workflow.add_conditional_edges(
        "send_offer",
        route_after_candidate_response,
        {
            "initiate_onboarding": "initiate_onboarding",
            "revise_offer": "revise_offer",
            "close_application": "close_application",
            END: END,
        },
    )

    # Negotiation: revise_offer loops back to offer_approval_interrupt
    workflow.add_edge("revise_offer", "offer_approval_interrupt")

    # Terminal edges
    workflow.add_edge("initiate_onboarding", END)
    workflow.add_edge("close_application", END)

    return workflow


def get_recruitment_app(checkpointer=None):
    """Compiles the master recruitment graph with persistent checkpointing."""
    cp = checkpointer or get_checkpointer()
    graph = create_recruitment_graph()
    return graph.compile(checkpointer=cp)
