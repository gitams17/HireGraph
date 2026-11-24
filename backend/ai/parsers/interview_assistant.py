from pydantic import BaseModel, Field


class SuggestedQuestion(BaseModel):
    id: str = Field(description="Unique question identifier, e.g. tech_1, beh_1")
    question: str = Field(description="The interview question text")
    category: str = Field(description="Category: technical, behavioural, project, or competency")
    evaluation_criteria: str = Field(description="Objective signals and criteria to evaluate in the candidate's response")
    follow_up_hint: str = Field(default="", description="Suggested follow-up probe or extension")


class InterviewQuestionsSchema(BaseModel):
    technical_questions: list[SuggestedQuestion] = Field(
        default_factory=list,
        description="Core technical depth, architecture, coding, and distributed systems questions",
    )
    behavioural_questions: list[SuggestedQuestion] = Field(
        default_factory=list,
        description="Situational, conflict resolution, ambiguity handling, and collaboration questions",
    )
    project_questions: list[SuggestedQuestion] = Field(
        default_factory=list,
        description="Deep dives into candidate's specific past projects, architecture decisions, and metrics",
    )
    competency_questions: list[SuggestedQuestion] = Field(
        default_factory=list,
        description="Role-specific domain competencies and standard engineering practices",
    )
