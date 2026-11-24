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
from ai.prompts.job_description import (
    JD_GENERATION_SYSTEM_PROMPT,
    JD_GENERATION_USER_PROMPT,
    JD_REVISION_SYSTEM_PROMPT,
    JD_REVISION_USER_PROMPT,
)


class BaseLLMProvider(Protocol):
    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        ...


class FakeLLMProvider:
    """Deterministic LLM Provider for testing and local development."""

    def __init__(self, mode: str = "success", custom_output: JobDescriptionSchema | None = None):
        self.mode = mode
        self.custom_output = custom_output

    def generate_job_description(self, requirements: dict[str, Any], feedback: str | None = None) -> JobDescriptionSchema:
        if self.mode == "error":
            raise RuntimeError("LLM API service unavailable.")

        if self.mode == "invalid_schema":
            # Return an invalid structure or raise validation error
            raise ValueError("LLM returned non-conforming schema structure.")

        if self.custom_output:
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


class GeminiProvider:
    """Google Gemini LLM Provider using langchain-google-genai."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str | None = None):
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=key, temperature=0.3)
        self.structured_llm = self.llm.with_structured_output(JobDescriptionSchema)

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

        result = self.structured_llm.invoke([sys_msg, HumanMessage(content=user_content)])
        return result


class OpenAIProvider:
    """OpenAI LLM Provider using langchain-openai."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str | None = None):
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model_name, api_key=key, temperature=0.3)
        self.structured_llm = self.llm.with_structured_output(JobDescriptionSchema)

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

        result = self.structured_llm.invoke([sys_msg, HumanMessage(content=user_content)])
        return result


def get_llm_provider(provider_type: str | None = None) -> BaseLLMProvider:
    """Factory to retrieve the configured LLM Provider."""
    chosen = (provider_type or os.getenv("LLM_PROVIDER", "fake")).strip().lower()

    if chosen == "gemini":
        return GeminiProvider()
    elif chosen == "openai":
        return OpenAIProvider()
    return FakeLLMProvider()
