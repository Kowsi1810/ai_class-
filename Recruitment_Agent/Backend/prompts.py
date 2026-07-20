"""
prompts.py

This file stores all prompts used by the AI Recruitment Agent.
Keeping prompts in one place makes them easy to update and maintain.
"""

from langchain_core.prompts import PromptTemplate


RANKING_PROMPT = PromptTemplate.from_template(
"""
You are an experienced HR recruiter.

Your task is to compare the following resume with the job description.

Job Description:
----------------
{job_description}

Resume:
--------
{resume}

Evaluate the candidate based on:

1. Technical Skills
2. Relevant Experience
3. Education
4. Projects
5. Certifications
6. Overall Match

Return the answer ONLY in this format.

Match Score: <number between 0 and 100>

Reason:
- ...
- ...
- ...

Strengths:
- ...
- ...

Weaknesses:
- ...
- ...
"""
)