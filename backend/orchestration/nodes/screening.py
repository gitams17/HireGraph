import logging
import os
from typing import Any

from ai.extractors.document import DocumentExtractionError, DocumentExtractor
from ai.providers.llm import get_llm_provider
from orchestration.state.resume_screening import ResumeScreeningState

logger = logging.getLogger(__name__)


def load_document_node(state: ResumeScreeningState) -> ResumeScreeningState:
    """Loads application, resume file reference, and job requirements."""
    from applications.models import Application

    app_id = state.get("application_id")
    try:
        app = Application.objects.select_related("job", "resume").get(id=app_id)
        resume = app.resume
        if not resume:
            return {
                **state,
                "status": "failed",
                "error": "No resume attached to this application.",
            }

        job = app.job
        job_requirements = {
            "title": job.title,
            "department": job.department,
            "employment_type": job.employment_type,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "required_skills": job.required_skills or [],
            "responsibilities": job.responsibilities or [],
        }

        return {
            **state,
            "resume_id": str(resume.id),
            "job_id": str(job.id),
            "file_path": resume.file.path,
            "filename": resume.file_name,
            "job_requirements": job_requirements,
            "status": "processing",
        }
    except Exception as e:
        logger.exception("Error in load_document_node for application %s", app_id)
        return {
            **state,
            "status": "failed",
            "error": f"Failed to load application data: {str(e)}",
        }


def extract_text_node(state: ResumeScreeningState) -> ResumeScreeningState:
    """Extracts text from PDF or DOCX file using DocumentExtractor."""
    if state.get("status") == "failed" or state.get("error"):
        return state

    file_path = state.get("file_path")
    try:
        extraction_result = DocumentExtractor.extract_from_file_path(file_path)
        cleaned_text = str(extraction_result["cleaned_text"])

        if len(cleaned_text.strip()) < 20:
            return {
                **state,
                "status": "failed",
                "error": "Document contains insufficient readable text. Scanned document requires OCR or valid text layer.",
            }

        return {
            **state,
            "raw_text": str(extraction_result["raw_text"]),
            "cleaned_text": cleaned_text,
            "is_scanned": bool(extraction_result["is_scanned"]),
            "injection_detected": bool(extraction_result["injection_detected"]),
        }
    except DocumentExtractionError as e:
        return {
            **state,
            "status": "failed",
            "error": str(e),
        }
    except Exception as e:
        logger.exception("Unexpected error extracting document text")
        return {
            **state,
            "status": "failed",
            "error": f"Failed to parse document: {str(e)}",
        }


def llm_extraction_node(state: ResumeScreeningState) -> ResumeScreeningState:
    """Invokes structured LLM extraction on cleaned resume text."""
    if state.get("status") == "failed" or state.get("error"):
        return state

    cleaned_text = state.get("cleaned_text", "")
    try:
        provider = get_llm_provider()
        parsed = provider.extract_resume(cleaned_text)
        return {
            **state,
            "extracted_data": parsed.model_dump(),
        }
    except Exception as e:
        logger.exception("Error in llm_extraction_node")
        return {
            **state,
            "status": "failed",
            "error": f"Failed to extract structured data from resume: {str(e)}",
        }


def evidence_evaluation_node(state: ResumeScreeningState) -> ResumeScreeningState:
    """Evaluates extracted candidate data against job requirements."""
    if state.get("status") == "failed" or state.get("error"):
        return state

    extracted_data = state.get("extracted_data", {})
    job_requirements = state.get("job_requirements", {})

    try:
        provider = get_llm_provider()
        assessment = provider.evaluate_candidate_resume(extracted_data, job_requirements)
        assessment_dict = assessment.model_dump()
        return {
            **state,
            "assessment": assessment_dict,
            "ats_score": assessment.ats_score,
            "status": "completed",
        }
    except Exception as e:
        logger.exception("Error in evidence_evaluation_node")
        return {
            **state,
            "status": "failed",
            "error": f"Failed to evaluate candidate against job requirements: {str(e)}",
        }


def save_assessment_node(state: ResumeScreeningState) -> ResumeScreeningState:
    """Persists ResumeAnalysis and logs ApplicationEvent in PostgreSQL."""
    from accounts.models import User
    from applications.models import Application, ApplicationEvent, ResumeAnalysis
    from candidates.models import Resume

    app_id = state.get("application_id")
    resume_id = state.get("resume_id")
    user_id = state.get("user_id")
    error = state.get("error")
    status_str = "failed" if error else "completed"

    try:
        app = Application.objects.get(id=app_id)
        resume = Resume.objects.get(id=resume_id) if resume_id else app.resume
        user = User.objects.filter(id=user_id).first() if user_id else None

        model_name = os.getenv("LLM_PROVIDER", "fake")

        analysis = ResumeAnalysis.objects.create(
            application=app,
            resume=resume,
            model_name=model_name,
            prompt_version="v1.0",
            evaluation_rubric_version="v1.0",
            extracted_data=state.get("extracted_data", {}),
            assessment=state.get("assessment", {}),
            ats_score=state.get("ats_score"),
            status=status_str,
            error_message=error or "",
        )

        ApplicationEvent.objects.create(
            application=app,
            event_type="ai_screening_completed" if not error else "ai_screening_failed",
            notes=(
                f"AI Screening completed with ATS Score: {state.get('ats_score')}/100"
                if not error
                else f"AI Screening failed: {error}"
            ),
            actor=user,
        )

        return {
            **state,
            "analysis_id": str(analysis.id),
            "status": status_str,
        }
    except Exception as e:
        logger.exception("Error in save_assessment_node")
        return {
            **state,
            "status": "failed",
            "error": f"Failed to save assessment: {str(e)}",
        }
