"""
LangGraph Job Description Workflow.
Compiles the StateGraph with interrupt-driven Human Approval, Checkpointing, and Revision loop.
"""

from typing import Literal
from langgraph.graph import END, StateGraph

from orchestration.nodes.approve import (
    approval_interrupt_node,
    mark_approved_node,
    ready_for_publication_node,
    save_version_node,
)
from orchestration.nodes.generate import generate_jd_node, load_requirements_node
from orchestration.nodes.revise import capture_feedback_node, generate_revision_node
from orchestration.state.hiring import HiringGraphState


def decide_route(state: HiringGraphState) -> Literal["mark_approved", "capture_feedback", "__end__"]:
    """Conditional router based on human approval decision."""
    if state.get("status") == "failed" or state.get("error"):
        return END

    decision = state.get("decision")
    if decision == "approved":
        return "mark_approved"
    elif decision == "rejected":
        return "capture_feedback"
    return END


def check_failure_after_generation(state: HiringGraphState) -> Literal["save_version", "__end__"]:
    if state.get("status") == "failed" or state.get("error"):
        return END
    return "save_version"


def create_job_description_graph():
    """Build and return the uncompiled StateGraph."""
    workflow = StateGraph(HiringGraphState)

    # Nodes
    workflow.add_node("load_requirements", load_requirements_node)
    workflow.add_node("generate_jd", generate_jd_node)
    workflow.add_node("save_version", save_version_node)
    workflow.add_node("approval_interrupt", approval_interrupt_node)
    workflow.add_node("mark_approved", mark_approved_node)
    workflow.add_node("ready_for_publication", ready_for_publication_node)
    workflow.add_node("capture_feedback", capture_feedback_node)
    workflow.add_node("generate_revision", generate_revision_node)

    # Edges
    workflow.set_entry_point("load_requirements")
    workflow.add_edge("load_requirements", "generate_jd")
    workflow.add_conditional_edges("generate_jd", check_failure_after_generation)
    workflow.add_edge("save_version", "approval_interrupt")

    # Conditional router after approval interrupt
    workflow.add_conditional_edges(
        "approval_interrupt",
        decide_route,
        {
            "mark_approved": "mark_approved",
            "capture_feedback": "capture_feedback",
            END: END,
        },
    )

    # Approval branch
    workflow.add_edge("mark_approved", "ready_for_publication")
    workflow.add_edge("ready_for_publication", END)

    # Revision branch: loops back to generate_jd
    workflow.add_edge("capture_feedback", "generate_revision")
    workflow.add_edge("generate_revision", "generate_jd")

    return workflow


def get_checkpointer(checkpointer_instance=None):
    """
    Returns an appropriate LangGraph checkpointer.
    If checkpointer_instance is provided (e.g. MemorySaver in tests), uses it.
    Otherwise, configures persistent PostgreSQL checkpointer via psycopg.
    """
    if checkpointer_instance is not None:
        return checkpointer_instance

    import os
    from langgraph.checkpoint.postgres import PostgresSaver

    # Construct DB connection string
    db_name = os.getenv("POSTGRES_DB", "hireflow")
    db_user = os.getenv("POSTGRES_USER", "hireflow")
    db_password = os.getenv("POSTGRES_PASSWORD", "local-db-password-change-me")
    db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    db_port = os.getenv("POSTGRES_PORT", "5432")

    conn_str = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    checkpointer_cm = PostgresSaver.from_conn_string(conn_str)
    return checkpointer_cm
