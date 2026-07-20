"""
ranking_tool.py

Uses the Groq LLM to rank resumes against
a job description.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from prompts import RANKING_PROMPT

# Load environment variables
load_dotenv()


class ResumeRankingTool:

    def __init__(self):
        """
        Initialize the Groq LLM.
        """

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY")
        )

    def rank_resume(self, job_description, resume_text):
        """
        Compare a resume with the job description.

        Parameters
        ----------
        job_description : str

        resume_text : str

        Returns
        -------
        str
        """

        prompt = RANKING_PROMPT.format(
            job_description=job_description,
            resume=resume_text
        )

        response = self.llm.invoke(prompt)

        return response.content