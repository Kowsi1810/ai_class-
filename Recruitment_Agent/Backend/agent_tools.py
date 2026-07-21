"""
agent_tools.py

Two separate toolkits, one per agent:

- SearchToolkit    -> one tool, search_resumes(query)
- EvaluationToolkit -> one tool, evaluate_candidate(filename)

Each toolkit is created fresh per request (see agents.py) so no
state — cached resume text, collected results — ever leaks between
unrelated requests.

Both toolkits collect the *structured* output of their tool calls
(SearchToolkit.candidates, EvaluationToolkit.evaluations) so the
orchestrator can read exact data back after each agent finishes,
instead of trusting either agent's own free-text final answer to
contain complete, valid JSON.
"""

import json

from langchain_core.tools import tool

from search_tool import ResumeSearchTool
from ranking_tool import ResumeRankingTool
from summary_tool import ResumeSummaryTool
from scoring import extract_match_score


class SearchToolkit:
    """
    Backs the Search Agent. Gives the LLM one tool, search_resumes,
    which it may call more than once (e.g. with a rephrased query)
    if it decides one search wasn't broad enough. Every candidate
    seen across all calls is accumulated into self.candidates.
    """

    def __init__(self):

        self.search_tool = ResumeSearchTool()

        self.candidates = {}  # filename -> full resume content, across all searches

    def build_tools(self):

        @tool
        def search_resumes(query: str) -> str:
            """
            Semantically search the resume database for candidates
            matching the given query. Returns a JSON list of
            {filename, preview}. You may call this more than once
            with a differently-phrased query (e.g. synonyms for the
            role) if you think the first search missed relevant
            candidates — results accumulate across calls.
            """

            found = self.search_tool.search_resumes(query)

            for c in found:
                self.candidates[c["filename"]] = c["content"]

            preview = [
                {"filename": c["filename"], "preview": c["content"][:220]}
                for c in found
            ]

            return json.dumps(preview)

        return [search_resumes]


class EvaluationToolkit:
    """
    Backs the Evaluation Agent. Gives the LLM one tool,
    evaluate_candidate, which scores, ranks, and summarizes one
    candidate at a time against a job description fixed for the
    whole evaluation run (set via job_description at construction,
    not passed as a tool argument — the Evaluation Agent is only
    ever evaluating candidates for one job description per call, so
    there's no reason to make the LLM repeat it on every tool call).
    """

    def __init__(self, job_description, candidate_pool):
        """
        candidate_pool : dict[filename, content]
            The full text of every candidate the Search Agent found,
            handed off from SearchToolkit.candidates.
        """

        self.job_description = job_description
        self.candidate_pool = candidate_pool

        self.ranking_tool = ResumeRankingTool()
        self.summary_tool = ResumeSummaryTool()

        self.evaluations = {}  # filename -> result, re-evaluating overwrites rather than duplicates

    def build_tools(self):

        @tool
        def evaluate_candidate(filename: str) -> str:
            """
            Score, rank, and summarize ONE candidate (by filename)
            against the job description for this evaluation run.
            `filename` must be one of the candidates handed to you.
            Returns a JSON object with match_score (0-100), ranking
            (the reasoning behind the score), and summary. Call this
            once per filename worth evaluating — skip any that are
            obviously irrelevant to save time.
            """

            resume_text = self.candidate_pool.get(filename)

            if resume_text is None:
                return json.dumps({
                    "error": (
                        f"Unknown filename '{filename}'. It wasn't "
                        "in the candidate pool handed to you."
                    )
                })

            ranking = self.ranking_tool.rank_resume(
                self.job_description, resume_text
            )

            match_score = extract_match_score(ranking)

            summary = self.summary_tool.summarize_resume(resume_text)

            result = {
                "filename": filename,
                "match_score": match_score,
                "ranking": ranking,
                "summary": summary,
            }

            self.evaluations[filename] = result

            return json.dumps(result)

        return [evaluate_candidate]
