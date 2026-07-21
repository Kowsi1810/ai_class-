"""
main.py

FastAPI application for the AI Recruitment Agent.
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import RecruitmentAgent
from schemas import JobDescriptionRequest, SearchResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recruitment_agent")

# -------------------------------------------------
# Create FastAPI App
# -------------------------------------------------

app = FastAPI(
    title="AI Recruitment Agent",
    description="Resume Search and Ranking API",
    version="1.0.0"
)

# -------------------------------------------------
# Allow React Frontend
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Initialize Agent
# -------------------------------------------------

agent = RecruitmentAgent()

# -------------------------------------------------
# Home
# -------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "AI Recruitment Agent API is Running"
    }

# -------------------------------------------------
# Health Check
# -------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "Healthy"
    }

# -------------------------------------------------
# Search Candidates
# -------------------------------------------------

@app.post("/search", response_model=SearchResponse)
def search_candidates(data: JobDescriptionRequest):

    if not data.job_description or not data.job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="job_description must not be empty."
        )

    try:
        results = agent.process_job_description(
            data.job_description,
            min_score=data.min_score
        )

    except Exception as exc:
        logger.exception("Failed to process job description")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process job description: {exc}"
        ) from exc

    return {
        "total_candidates": len(results),
        "results": results
    }