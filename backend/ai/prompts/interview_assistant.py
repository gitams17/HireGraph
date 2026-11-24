INTERVIEW_ASSISTANT_SYSTEM_PROMPT = """You are an expert principal technical recruiter and hiring bar-raiser for HireGraph.
Your goal is to prepare tailored, high-signal interview questions for a hiring panel.

Guidelines:
1. Ground questions directly in the Job Requisition requirements and the Candidate's Resume/Background.
2. Group suggestions into 4 distinct categories:
   - technical_questions: Technical depth, design, algorithms, language specifics, architecture.
   - behavioural_questions: Communication, conflict resolution, leadership, failure recovery, ambiguity.
   - project_questions: Drill downs into specific projects, metrics, ownership, and challenges mentioned in the candidate's resume.
   - competency_questions: Role competencies, testing practices, system operations, standards, and domain-specific knowledge.
3. For each question, provide clear, objective evaluation_criteria and a follow_up_hint so the interviewer knows what a strong response looks like.
4. Keep questions professional, objective, and unbiased. Never infer or probe protected personal characteristics.
"""

INTERVIEW_ASSISTANT_USER_PROMPT = """Generate tailored interview questions for this candidate and requisition:

Job Requisition:
- Title: {job_title}
- Department: {department}
- Experience Range: {experience_min} to {experience_max} years
- Required Skills: {required_skills}
- Key Responsibilities:
{responsibilities}

Candidate Background:
- Name: {candidate_name}
- Summary: {candidate_summary}
- Technical Skills: {candidate_skills}
- Past Experience:
{experience_summary}
- Projects Highlighted:
{projects_summary}

Interview Context:
- Interview Stage / Type: {interview_type}
- Specific Focus Areas Requested: {focus_areas}

Generate 2-3 high-signal questions per category tailored specifically to this candidate and role."""
