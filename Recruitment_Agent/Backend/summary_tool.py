"""
summary_tool.py

Generate a professional summary of a resume
using Groq LLM.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()


SUMMARY_PROMPT = PromptTemplate.from_template(
"""
You are an expert HR Recruiter.

Read the resume below.

Resume
-------
{resume}

Generate a professional summary using the following format.

Candidate Summary

Name :
Experience :
Education :
Technical Skills :
Soft Skills :
Projects :
Certifications :
Strengths :
Weaknesses :
Overall Summary :

Keep the response concise and professional.
"""
)


class ResumeSummaryTool:

    def __init__(self):

        self.llm = ChatGroq(

            model="llama-3.3-70b-versatile",

            temperature=0,

            api_key=os.getenv("GROQ_API_KEY")

        )

    def summarize_resume(self, resume_text):

        prompt = SUMMARY_PROMPT.format(

            resume=resume_text

        )

        response = self.llm.invoke(prompt)

        return response.content