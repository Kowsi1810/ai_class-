"""
models.py

Business models used inside the AI Recruitment Agent.

These are not database models.
They represent the information returned
by the AI tools.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Candidate:

    filename: str

    resume_text: str

    ranking: str

    summary: str


@dataclass
class SearchResult:

    candidates: List[Candidate]