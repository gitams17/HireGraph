"""
LLM Provider Abstraction layer.
Supports:
- GeminiProvider (Google Gemini via langchain-google-genai)
- OpenAIProvider (OpenAI via langchain-openai)
- FakeLLMProvider (Deterministic mock for test isolation & 0-cost verification)
"""

import os
from typing import Any, Protocol

from ai.parsers.job_description import JobDescriptionSchema
from ai.parsers.resume_screening import (
    CandidateAssessmentSchema,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    ParsedResumeSchema,
    ProjectItem,
    SkillEvidence,
)
from ai.prompts.job_description import (
    JD_GENERATION_SYSTEM_PROMPT,
    JD_GENERATION_USER_PROMPT,
    JD_REVISION_SYSTEM_PROMPT,
    JD_REVISION_USER_PROMPT,
)
from ai.prompts.resume_screening import (
    RESUME_EVALUATION_SYSTEM_PROMPT,
    RESUME_EVALUATION_USER_PROMPT,
    RESUME_EXTRACTION_SYSTEM_PROMPT,
    RESUME_EXTRACTION_USER_PROMPT,
)


class BaseLLMProvider(Protocol):
    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        ...

    def extract_resume(self, cleaned_text: str) -> ParsedResumeSchema:
        ...

    def evaluate_candidate_resume(self, parsed_resume: dict[str, Any], requirements: dict[str, Any]) -> CandidateAssessmentSchema:
        ...


class FakeLLMProvider:
    """Deterministic LLM Provider for testing and local development."""

    def __init__(self, mode: str = "success", custom_output: Any = None):
        self.mode = mode
        self.custom_output = custom_output

    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        if self.mode == "error":
            raise RuntimeError("LLM API service unavailable.")

        if self.mode == "invalid_schema":
            raise ValueError("LLM returned non-conforming schema structure.")

        if self.custom_output and isinstance(self.custom_output, JobDescriptionSchema):
            return self.custom_output

        title = requirements.get("title", "Software Engineer")
        department = requirements.get("department", "Engineering")
        skills = requirements.get("required_skills", ["Python", "Django"])
        responsibilities = requirements.get("responsibilities", ["Build scalable APIs"])

        if feedback:
            overview = f"Revised overview for {title} in {department}. Addressed feedback: {feedback}"
        else:
            overview = f"We are seeking a talented {title} to join our {department} team. You will drive innovation and deliver robust software solutions."

        return JobDescriptionSchema(
            title=title,
            overview=overview,
            responsibilities=responsibilities if isinstance(responsibilities, list) else [str(responsibilities)],
            required_qualifications=skills if isinstance(skills, list) else [str(skills)],
            preferred_qualifications=["Experience with Cloud services (AWS/GCP)", "Agile workflows"],
            benefits=["Competitive salary & equity", "Comprehensive health coverage", "Flexible remote work", "Learning stipend"],
        )

    def extract_resume(self, cleaned_text: str) -> ParsedResumeSchema:
        if self.mode == "error":
            raise RuntimeError("LLM API service unavailable.")
        if self.mode == "invalid_schema":
            raise ValueError("LLM returned non-conforming schema structure.")
        if self.custom_output and isinstance(self.custom_output, ParsedResumeSchema):
            return self.custom_output

        return ParsedResumeSchema(
            candidate_name="Alex Rivera",
            email="alex.rivera@example.com",
            phone="+1-555-0199",
            location="San Francisco, CA",
            summary="Senior Software Engineer with 5+ years of experience designing scalable distributed architectures in Python and Django.",
            technical_skills=["Python", "Django", "PostgreSQL", "React", "TypeScript", "Docker", "AWS"],
            soft_skills=["Mentorship", "Cross-functional Collaboration", "Agile Leadership"],
            education=[
                EducationItem(
                    institution="Stanford University",
                    degree="Bachelor of Science",
                    field_of_study="Computer Science",
                    start_year=2015,
                    end_year=2019,
                )
            ],
            experience=[
                ExperienceItem(
                    company="Acme Cloud",
                    title="Senior Software Engineer",
                    start_date="Jan 2021",
                    end_date="Present",
                    is_current=True,
                    description="Architected high-throughput Django REST endpoints and streamlined Postgres query performance.",
                    technologies_used=["Python", "Django", "PostgreSQL", "Redis", "Docker"],
                )
            ],
            projects=[
                ProjectItem(
                    name="HireGraph Engine",
                    description="Automated recruitment workflow graph running on LangGraph and Celery.",
                    technologies=["Python", "LangGraph", "Celery", "PostgreSQL"],
                )
            ],
            certifications=[
                CertificationItem(
                    name="AWS Certified Solutions Architect",
                    issuer="Amazon Web Services",
                    issue_year=2022,
                )
            ],
        )

    def evaluate_candidate_resume(self, parsed_resume: dict[str, Any], requirements: dict[str, Any]) -> CandidateAssessmentSchema:
        if self.mode == "error":
            raise RuntimeError("LLM API service unavailable.")
        if self.mode == "invalid_schema":
            raise ValueError("LLM returned non-conforming schema structure.")
        if self.custom_output and isinstance(self.custom_output, CandidateAssessmentSchema):
            return self.custom_output

        req_skills = requirements.get("required_skills", ["Python", "Django"])
        cand_skills = [str(s).lower() for s in parsed_resume.get("technical_skills", [])]

        skill_evals: list[SkillEvidence] = []
        found_count = 0
        for skill in req_skills:
            if str(skill).lower() in cand_skills:
                found_count += 1
                skill_evals.append(
                    SkillEvidence(
                        skill=skill,
                        status="found",
                        evidence=f"Evidence found in work experience and projects mentioning {skill}.",
                    )
                )
            else:
                skill_evals.append(
                    SkillEvidence(
                        skill=skill,
                        status="missing",
                        evidence=f"No direct evidence found for '{skill}' in candidate resume.",
                    )
                )

        total_req = len(req_skills) or 1
        ats_score = int((found_count / total_req) * 85) + 12
        ats_score = min(max(ats_score, 30), 96)

        rec: Any = "strong_match" if ats_score >= 80 else ("potential_match" if ats_score >= 60 else "requires_human_review")

        return CandidateAssessmentSchema(
            ats_score=ats_score,
            summary_headline=f"Candidate demonstrates evidence for {found_count} of {len(req_skills)} required technical skills.",
            required_skills_evaluation=skill_evals,
            relevant_experience_summary="Strong software engineering background matching backend and systems architecture requirements.",
            missing_evidence=[e.skill for e in skill_evals if e.status == "missing"],
            strengths=["Deep experience with core required backend languages", "Hands-on projects with modern tooling"],
            concerns_or_gaps=["Confirm production deployment scale during live technical screen"],
            reviewer_recommendation=rec,
            recommendation_rationale="Candidate meets all foundational technical requirements. Human interview recommended.",
        )


class GeminiProvider:
    """Google Gemini LLM Provider using langchain-google-genai."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str | None = None):
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=key, temperature=0.2)
        self.structured_jd = self.llm.with_structured_output(JobDescriptionSchema)
        self.structured_extraction = self.llm.with_structured_output(ParsedResumeSchema)
        self.structured_evaluation = self.llm.with_structured_output(CandidateAssessmentSchema)

    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        from langchain_core.messages import HumanMessage, SystemMessage

        if feedback and requirements.get("previous_jd"):
            sys_msg = SystemMessage(content=JD_REVISION_SYSTEM_PROMPT)
            user_content = JD_REVISION_USER_PROMPT.format(
                previous_jd=requirements.get("previous_jd", ""),
                feedback=feedback,
                title=requirements.get("title", ""),
                department=requirements.get("department", ""),
                location=requirements.get("location", ""),
                employment_type=requirements.get("employment_type", ""),
                required_skills=", ".join(requirements.get("required_skills", [])),
                responsibilities="\n".join(requirements.get("responsibilities", [])),
            )
        else:
            sys_msg = SystemMessage(content=JD_GENERATION_SYSTEM_PROMPT)
            user_content = JD_GENERATION_USER_PROMPT.format(
                title=requirements.get("title", ""),
                department=requirements.get("department", ""),
                location=requirements.get("location", ""),
                employment_type=requirements.get("employment_type", ""),
                experience_min=requirements.get("experience_min") or "Not specified",
                experience_max=requirements.get("experience_max") or "Not specified",
                required_skills=", ".join(requirements.get("required_skills", [])),
                responsibilities="\n".join(requirements.get("responsibilities", [])),
            )

        return self.structured_jd.invoke([sys_msg, HumanMessage(content=user_content)])

    def extract_resume(self, cleaned_text: str) -> ParsedResumeSchema:
        from langchain_core.messages import HumanMessage, SystemMessage
        sys_msg = SystemMessage(content=RESUME_EXTRACTION_SYSTEM_PROMPT)
        user_msg = HumanMessage(content=RESUME_EXTRACTION_USER_PROMPT.format(cleaned_text=cleaned_text))
        return self.structured_extraction.invoke([sys_msg, user_msg])

    def evaluate_candidate_resume(self, parsed_resume: dict[str, Any], requirements: dict[str, Any]) -> CandidateAssessmentSchema:
        from langchain_core.messages import HumanMessage, SystemMessage
        sys_msg = SystemMessage(content=RESUME_EVALUATION_SYSTEM_PROMPT)

        user_content = RESUME_EVALUATION_USER_PROMPT.format(
            job_title=requirements.get("title", ""),
            department=requirements.get("department", "General"),
            employment_type=requirements.get("employment_type", "Full-time"),
            experience_min=requirements.get("experience_min") or 0,
            experience_max=requirements.get("experience_max") or "Unspecified",
            required_skills="\n- ".join([""] + requirements.get("required_skills", [])),
            responsibilities="\n- ".join([""] + requirements.get("responsibilities", [])),
            candidate_name=parsed_resume.get("candidate_name", "Candidate"),
            summary=parsed_resume.get("summary", ""),
            technical_skills=", ".join(parsed_resume.get("technical_skills", [])),
            experience_summary="\n".join(
                [f"- {e.get('title')} at {e.get('company')}: {e.get('description', '')}" for e in parsed_resume.get("experience", [])]
            ),
            projects_summary="\n".join(
                [f"- {p.get('name')}: {p.get('description', '')} ({', '.join(p.get('technologies', []))})" for p in parsed_resume.get("projects", [])]
            ),
            education_summary="\n".join(
                [f"- {ed.get('degree')} in {ed.get('field_of_study')} from {ed.get('institution')}" for ed in parsed_resume.get("education", [])]
            ),
            certifications_summary="\n".join(
                [f"- {c.get('name')} ({c.get('issuer')})" for c in parsed_resume.get("certifications", [])]
            ),
        )

        return self.structured_evaluation.invoke([sys_msg, HumanMessage(content=user_content)])


class OpenAIProvider:
    """OpenAI LLM Provider using langchain-openai."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str | None = None):
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model_name, api_key=key, temperature=0.2)
        self.structured_jd = self.llm.with_structured_output(JobDescriptionSchema)
        self.structured_extraction = self.llm.with_structured_output(ParsedResumeSchema)
        self.structured_evaluation = self.llm.with_structured_output(CandidateAssessmentSchema)

    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        from langchain_core.messages import HumanMessage, SystemMessage

        if feedback and requirements.get("previous_jd"):
            sys_msg = SystemMessage(content=JD_REVISION_SYSTEM_PROMPT)
            user_content = JD_REVISION_USER_PROMPT.format(
                previous_jd=requirements.get("previous_jd", ""),
                feedback=feedback,
                title=requirements.get("title", ""),
                department=requirements.get("department", ""),
                location=requirements.get("location", ""),
                employment_type=requirements.get("employment_type", ""),
                required_skills=", ".join(requirements.get("required_skills", [])),
                responsibilities="\n".join(requirements.get("responsibilities", [])),
            )
        else:
            sys_msg = SystemMessage(content=JD_GENERATION_SYSTEM_PROMPT)
            user_content = JD_GENERATION_USER_PROMPT.format(
                title=requirements.get("title", ""),
                department=requirements.get("department", ""),
                location=requirements.get("location", ""),
                employment_type=requirements.get("employment_type", ""),
                experience_min=requirements.get("experience_min") or "Not specified",
                experience_max=requirements.get("experience_max") or "Not specified",
                required_skills=", ".join(requirements.get("required_skills", [])),
                responsibilities="\n".join(requirements.get("responsibilities", [])),
            )

        return self.structured_jd.invoke([sys_msg, HumanMessage(content=user_content)])

    def extract_resume(self, cleaned_text: str) -> ParsedResumeSchema:
        from langchain_core.messages import HumanMessage, SystemMessage
        sys_msg = SystemMessage(content=RESUME_EXTRACTION_SYSTEM_PROMPT)
        user_msg = HumanMessage(content=RESUME_EXTRACTION_USER_PROMPT.format(cleaned_text=cleaned_text))
        return self.structured_extraction.invoke([sys_msg, user_msg])

    def evaluate_candidate_resume(self, parsed_resume: dict[str, Any], requirements: dict[str, Any]) -> CandidateAssessmentSchema:
        from langchain_core.messages import HumanMessage, SystemMessage
        sys_msg = SystemMessage(content=RESUME_EVALUATION_SYSTEM_PROMPT)

        user_content = RESUME_EVALUATION_USER_PROMPT.format(
            job_title=requirements.get("title", ""),
            department=requirements.get("department", "General"),
            employment_type=requirements.get("employment_type", "Full-time"),
            experience_min=requirements.get("experience_min") or 0,
            experience_max=requirements.get("experience_max") or "Unspecified",
            required_skills="\n- ".join([""] + requirements.get("required_skills", [])),
            responsibilities="\n- ".join([""] + requirements.get("responsibilities", [])),
            candidate_name=parsed_resume.get("candidate_name", "Candidate"),
            summary=parsed_resume.get("summary", ""),
            technical_skills=", ".join(parsed_resume.get("technical_skills", [])),
            experience_summary="\n".join(
                [f"- {e.get('title')} at {e.get('company')}: {e.get('description', '')}" for e in parsed_resume.get("experience", [])]
            ),
            projects_summary="\n".join(
                [f"- {p.get('name')}: {p.get('description', '')} ({', '.join(p.get('technologies', []))})" for p in parsed_resume.get("projects", [])]
            ),
            education_summary="\n".join(
                [f"- {ed.get('degree')} in {ed.get('field_of_study')} from {ed.get('institution')}" for ed in parsed_resume.get("education", [])]
            ),
            certifications_summary="\n".join(
                [f"- {c.get('name')} ({c.get('issuer')})" for c in parsed_resume.get("certifications", [])]
            ),
        )

        return self.structured_evaluation.invoke([sys_msg, HumanMessage(content=user_content)])


def get_llm_provider(provider_type: str | None = None) -> BaseLLMProvider:
    """Factory to retrieve the configured LLM Provider."""
    chosen = (provider_type or os.getenv("LLM_PROVIDER", "fake")).strip().lower()

    if chosen == "gemini":
        return GeminiProvider()
    elif chosen == "openai":
        return OpenAIProvider()
    return FakeLLMProvider()
