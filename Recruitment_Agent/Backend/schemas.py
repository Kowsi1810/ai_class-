"""
schemas.py

This file contains all the request and response
schemas used by the FastAPI application.
"""

from pydantic import BaseModel
from typing import List


# ----------------------------------------
# Request Schema
# ----------------------------------------

class JobDescriptionRequest(BaseModel):
    """
    Request body for searching resumes.
    """

    job_description: str

    min_score: int = 50
    """Minimum match score (0-100) a candidate must have to be returned."""


# ----------------------------------------
# Candidate Schema
# ----------------------------------------

class CandidateResult(BaseModel):
    """
    Single candidate information.
    """

    filename: str

    match_score: int

    ranking: str

    summary: str


# ----------------------------------------
# Response Schema
# ----------------------------------------

class SearchResponse(BaseModel):
    """
    API response after searching resumes.
    """

    total_candidates: int

    results: List[CandidateResult]