from typing import Any
from ai.parsers.job_description import JobDescriptionSchema
from ai.providers.llm import get_llm_provider
from orchestration.state.hiring import HiringGraphState


def load_requirements_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Fetch requirements from JobRequisition if not already in state."""
    job_id = state.get("job_id")
    if not job_id:
        return {"error": "Missing job_id in state", "status": "failed"}

    # If requirements not already passed, load from Django ORM
    requirements = state.get("requirements")
    if not requirements:
        from jobs.models import JobRequisition
        try:
            job = JobRequisition.objects.select_related("organization").get(id=job_id)
            requirements = {
                "id": str(job.id),
                "organization_id": str(job.organization_id),
                "title": job.title,
                "department": job.department,
                "location": job.location,
                "employment_type": job.employment_type,
                "experience_min": job.experience_min,
                "experience_max": job.experience_max,
                "required_skills": job.required_skills,
                "responsibilities": job.responsibilities,
            }
        except Exception as e:
            return {"error": f"Failed to load job requisition: {e}", "status": "failed"}

    return {
        "requirements": requirements,
        "organization_id": requirements.get("organization_id", state.get("organization_id", "")),
        "status": "requirements_loaded",
    }


def generate_jd_node(state: HiringGraphState) -> dict[str, Any]:
    """Node: Invoke LLM to generate structured Job Description and validate."""
    requirements = state.get("requirements", {})
    feedback = state.get("feedback")
    provider = get_llm_provider()

    try:
        jd_schema: JobDescriptionSchema = provider.generate_job_description(requirements, feedback=feedback)
        jd_dict = jd_schema.model_dump()
        raw_md = jd_schema.to_markdown()

        return {
            "generated_jd": jd_dict,
            "raw_markdown": raw_md,
            "status": "jd_generated",
            "error": None,
        }
    except Exception as e:
        return {
            "error": f"LLM generation failed: {e}",
            "status": "failed",
        }
