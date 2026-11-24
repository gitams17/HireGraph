"""
Prompt templates for Job Description Generation and Revision.
"""

JD_GENERATION_SYSTEM_PROMPT = """You are an expert talent acquisition specialist and executive recruiter.
Your objective is to craft an engaging, inclusive, and highly accurate job description based on the provided hiring requirements.

Guidelines:
1. Overview: Provide a concise, inspiring 2-3 paragraph summary of the role's mission and team context.
2. Responsibilities: Detail concrete, realistic expectations and day-to-day impact.
3. Required Qualifications: Clearly separate essential must-haves (matching the specified experience level and skills).
4. Preferred Qualifications: Include realistic nice-to-haves that set top candidates apart.
5. Benefits & Perks: Highlight competitive perks, remote flexibility, and growth opportunities.

Ensure all output adheres strictly to the requested schema.
"""

JD_GENERATION_USER_PROMPT = """Create a structured job description for the following requisition:

Title: {title}
Department: {department}
Location: {location}
Employment Type: {employment_type}
Experience Range: {experience_min} to {experience_max} years
Required Skills: {required_skills}
Key Responsibilities Outline: {responsibilities}
"""

JD_REVISION_SYSTEM_PROMPT = """You are an expert talent acquisition specialist revising a job description based on hiring manager feedback.
Refine the job description to address every specific point of feedback while preserving accurate role requirements.
"""

JD_REVISION_USER_PROMPT = """Please revise the previous job description based on the hiring manager's feedback.

Current Job Description:
{previous_jd}

Hiring Manager Feedback:
{feedback}

Original Requirements:
Title: {title}
Department: {department}
Location: {location}
Employment Type: {employment_type}
Required Skills: {required_skills}
Key Responsibilities: {responsibilities}
"""
