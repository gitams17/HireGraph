"""
LangGraph Resume Screening Workflow.
Compiles the StateGraph for document parsing, structured LLM extraction,
evidence-based evaluation, and PostgreSQL persistence.
"""

from typing import Literal
from langgraph.graph import END, StateGraph

from orchestration.nodes.screening import (
    evidence_evaluation_node,
    extract_text_node,
    llm_extraction_node,
    load_document_node,
    save_assessment_node,
)
from orchestration.state.resume_screening import ResumeScreeningState


def check_failure_after_load(state: ResumeScreeningState) -> Literal["extract_text", "save_assessment"]:
    if state.get("status") == "failed" or state.get("error"):
        return "save_assessment"
    return "extract_text"


def check_failure_after_extract(state: ResumeScreeningState) -> Literal["llm_extraction", "save_assessment"]:
    if state.get("status") == "failed" or state.get("error"):
        return "save_assessment"
    return "llm_extraction"


def check_failure_after_extraction(state: ResumeScreeningState) -> Literal["evidence_evaluation", "save_assessment"]:
    if state.get("status") == "failed" or state.get("error"):
        return "save_assessment"
    return "evidence_evaluation"


def create_resume_screening_graph():
    """Build and return the uncompiled StateGraph for resume screening."""
    workflow = StateGraph(ResumeScreeningState)

    # Nodes
    workflow.add_node("load_document", load_document_node)
    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("llm_extraction", llm_extraction_node)
    workflow.add_node("evidence_evaluation", evidence_evaluation_node)
    workflow.add_node("save_assessment", save_assessment_node)

    # Edges
    workflow.set_entry_point("load_document")
    workflow.add_conditional_edges("load_document", check_failure_after_load)
    workflow.add_conditional_edges("extract_text", check_failure_after_extract)
    workflow.add_conditional_edges("llm_extraction", check_failure_after_extraction)
    workflow.add_edge("evidence_evaluation", "save_assessment")
    workflow.add_edge("save_assessment", END)

    return workflow


def get_resume_screening_app():
    """Compiles and returns the runnable LangGraph workflow."""
    workflow = create_resume_screening_graph()
    return workflow.compile()
