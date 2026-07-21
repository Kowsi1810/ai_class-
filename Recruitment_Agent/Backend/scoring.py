"""
scoring.py

Shared helper for pulling the numeric "Match Score: N" the ranking
LLM writes out of its free-text response. Used by both the tool
(agent_tools.py) and the agent orchestrator (agents.py), so there is
exactly one place this parsing logic lives.
"""

import re

MATCH_SCORE_PATTERN = re.compile(r"Match Score:\s*(\d{1,3})", re.IGNORECASE)


def extract_match_score(ranking_text):
    """
    Returns 0 if no score could be parsed, so a malformed LLM
    response never crashes the request — it just sorts/filters last.
    """

    match = MATCH_SCORE_PATTERN.search(ranking_text or "")

    if not match:
        return 0

    score = int(match.group(1))

    return max(0, min(score, 100))
