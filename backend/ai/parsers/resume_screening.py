from typing import Literal
from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    institution: str = Field(description="Name of the university, college, or school")
    degree: str = Field(description="Degree or credential (e.g., Bachelor of Science, Master of Engineering)")
    field_of_study: str = Field(default="", description="Major or area of study")
    start_year: int | None = Field(default=None, description="Start year if mentioned")
    end_year: int | None = Field(default=None, description="Graduation or end year if mentioned")
    grade_or_gpa: str | None = Field(default=None, description="GPA or grade if mentioned")


class ExperienceItem(BaseModel):
    company: str = Field(description="Name of the organization or employer")
    title: str = Field(description="Job title or role held")
    start_date: str | None = Field(default=None, description="Start date (e.g. 'Jan 2021')")
    end_date: str | None = Field(default=None, description="End date (e.g. 'Present' or 'Dec 2023')")
    is_current: bool = Field(default=False, description="True if this is the candidate's current position")
    description: str = Field(default="", description="Summary of work performed and key accomplishments")
    technologies_used: list[str] = Field(default_factory=list, description="Technologies, languages, or tools mentioned")


class ProjectItem(BaseModel):
    name: str = Field(description="Name of the project")
    description: str = Field(default="", description="Description of the project and impact")
    technologies: list[str] = Field(default_factory=list, description="Technologies or tools used")
    url: str | None = Field(default=None, description="Repository or project URL if provided")


class CertificationItem(BaseModel):
    name: str = Field(description="Certification title")
    issuer: str = Field(default="", description="Issuing body (e.g., AWS, Google Cloud, Cisco)")
    issue_year: int | None = Field(default=None, description="Year obtained")


class ParsedResumeSchema(BaseModel):
    candidate_name: str = Field(description="Full name of the candidate")
    email: str | None = Field(default=None, description="Email address if present")
    phone: str | None = Field(default=None, description="Phone number if present")
    location: str | None = Field(default=None, description="Location or city/country")
    summary: str = Field(default="", description="Professional summary or profile")
    technical_skills: list[str] = Field(default_factory=list, description="List of technical and hard skills")
    soft_skills: list[str] = Field(default_factory=list, description="List of interpersonal and communication skills")
    education: list[EducationItem] = Field(default_factory=list, description="Educational background")
    experience: list[ExperienceItem] = Field(default_factory=list, description="Chronological work history")
    projects: list[ProjectItem] = Field(default_factory=list, description="Notable personal or professional projects")
    certifications: list[CertificationItem] = Field(default_factory=list, description="Professional certifications")


class SkillEvidence(BaseModel):
    skill: str = Field(description="The required skill from the job requisition")
    status: Literal["found", "partial", "missing"] = Field(
        description="Whether verifiable evidence was found in the resume"
    )
    evidence: str = Field(
        description="Direct citation or explanation of evidence found in work experience or projects. If missing, explain what was absent."
    )


class CandidateAssessmentSchema(BaseModel):
    ats_score: int = Field(
        ge=0,
        le=100,
        description="Advisory matching score from 0 to 100 based on requirements rubric",
    )
    summary_headline: str = Field(
        description="One-sentence executive summary of the candidate's alignment"
    )
    required_skills_evaluation: list[SkillEvidence] = Field(
        description="Evidence-based breakdown for each required job skill"
    )
    relevant_experience_summary: str = Field(
        description="Synthesis of how past roles align with the target position responsibilities"
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="List of required qualifications or skills with no verifiable evidence in the resume",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Key strengths directly substantiated by the resume",
    )
    concerns_or_gaps: list[str] = Field(
        default_factory=list,
        description="Potential gaps, missing requirements, or areas needing human interview probing",
    )
    reviewer_recommendation: Literal[
        "strong_match",
        "potential_match",
        "requires_human_review",
        "does_not_meet_minimum",
    ] = Field(
        description="Advisory recommendation for human recruiter review"
    )
    recommendation_rationale: str = Field(
        description="Detailed rationale explaining the recommendation and highlights for recruiter review"
    )
