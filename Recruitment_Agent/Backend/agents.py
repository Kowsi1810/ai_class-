"""
agents.py

Three things live here:

- SearchAgent
    A real LangChain agent (create_agent). Given a job description,
    it decides for itself whether one search is enough or whether to
    search again with different phrasing to widen coverage. Its only
    tool is search_resumes. It never ranks or summarizes anything.

- EvaluationAgent
    A second, separate real LangChain agent. Given a job description
    and the pool of candidates the Search Agent found, it decides
    for itself which candidates are worth fully evaluating and calls
    evaluate_candidate (rank + summarize) for each. It never searches.

- RecruitmentAgent
    A small, plain-Python orchestrator — NOT itself an LLM agent —
    that runs SearchAgent, hands its output to EvaluationAgent, and
    returns the filtered/sorted results. This is what main.py calls.
    It exists purely to wire two independent agents together; it
    makes no LLM calls and no decisions of its own.

- RecruitmentPipeline
    The original fully deterministic version (search -> rank ->
    summarize every result, always), kept for comparison / fallback.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from search_tool import ResumeSearchTool
from ranking_tool import ResumeRankingTool
from summary_tool import ResumeSummaryTool
from agent_tools import SearchToolkit, EvaluationToolkit
from scoring import extract_match_score
from config import MIN_MATCH_SCORE

load_dotenv()


SEARCH_AGENT_SYSTEM_PROMPT = """\
You are a candidate-sourcing agent. Given a job description, your \
only job is to find candidates in the resume database who could \
plausibly match it — you do NOT rank, score, or summarize anyone.

You have one tool: search_resumes(query).

- Call it at least once with a query based on the job description.
- If you think the role could be described with different wording \
(e.g. "frontend developer" vs "web developer" vs "React developer"), \
call search_resumes again with the alternate phrasing to widen \
coverage. Don't overdo it — 1 to 3 searches is normally enough.
- When you're confident you've found the relevant candidates, stop \
calling tools and briefly state how many candidates you found.
"""

EVALUATION_AGENT_SYSTEM_PROMPT = """\
You are a candidate-evaluation agent. You will be given a job \
description and a list of candidate filenames with short previews. \
Your only job is to decide which of them are worth fully evaluating, \
and evaluate each with your tool — you do NOT search for candidates.

You have one tool: evaluate_candidate(filename).

- If a candidate's preview is obviously unrelated to the role (a \
completely different field, no relevant keywords at all), you may \
skip it to save time.
- Otherwise, call evaluate_candidate for it.
- Never call evaluate_candidate on a filename you weren't given.
- Never evaluate the same filename twice.
- Once you've evaluated every plausible candidate, stop calling \
tools and briefly summarize what you found.
"""


class SearchAgent:
    """Real LLM agent: decides how many times to search, and how."""

    def __init__(self, llm):
        self.llm = llm

    def run(self, job_description):
        """
        Returns dict[filename, content] — every candidate found
        across however many searches the agent decided to run.
        """

        toolkit = SearchToolkit()
        tools = toolkit.build_tools()

        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
        )

        agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"Job description:\n{job_description}"
            }]
        })

        return toolkit.candidates


class EvaluationAgent:
    """Real LLM agent: decides which candidates are worth evaluating."""

    def __init__(self, llm):
        self.llm = llm

    def run(self, job_description, candidate_pool):
        """
        candidate_pool : dict[filename, content] from SearchAgent.run()

        Returns dict[filename, result] for every candidate the agent
        chose to evaluate.
        """

        if not candidate_pool:
            return {}

        toolkit = EvaluationToolkit(job_description, candidate_pool)
        tools = toolkit.build_tools()

        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=EVALUATION_AGENT_SYSTEM_PROMPT,
        )

        preview_list = "\n".join(
            f"- {filename}: {content[:220]}"
            for filename, content in candidate_pool.items()
        )

        agent.invoke({
            "messages": [{
                "role": "user",
                "content": (
                    f"Job description:\n{job_description}\n\n"
                    f"Candidates found:\n{preview_list}"
                )
            }]
        })

        return toolkit.evaluations


class RecruitmentAgent:
    """
    Plain-Python orchestrator connecting SearchAgent -> EvaluationAgent.
    Not an LLM agent itself — it makes no model calls and no
    decisions; it just passes data from one real agent to the other.
    This is what main.py calls.
    """

    def __init__(self):

        print("=" * 60)
        print("Initializing Recruitment Agent (Search + Evaluation)...")
        print("=" * 60)

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.search_agent = SearchAgent(llm)
        self.evaluation_agent = EvaluationAgent(llm)

        print("Recruitment Agent Ready!")
        print("=" * 60)

    def process_job_description(self, job_description, min_score=None):

        if min_score is None:
            min_score = MIN_MATCH_SCORE

        print("\n" + "=" * 60)
        print("JOB DESCRIPTION")
        print("=" * 60)
        print(job_description)

        print("\n[Search Agent] running...")
        candidate_pool = self.search_agent.run(job_description)
        print(f"[Search Agent] found {len(candidate_pool)} candidate(s)")

        print("\n[Evaluation Agent] running...")
        evaluations = self.evaluation_agent.run(job_description, candidate_pool)
        print(f"[Evaluation Agent] evaluated {len(evaluations)} candidate(s)")

        results = list(evaluations.values())

        filtered = [r for r in results if r["match_score"] >= min_score]
        filtered.sort(key=lambda r: r["match_score"], reverse=True)

        print(f"\nCandidates above threshold ({min_score}): {len(filtered)}")
        print("=" * 60)

        return filtered


class RecruitmentPipeline:
    """
    The original fully deterministic pipeline (search -> rank ->
    summarize every result, always, in that order). No agents at
    all — kept for comparison / fallback.
    """

    def __init__(self):

        self.search_tool = ResumeSearchTool()
        self.ranking_tool = ResumeRankingTool()
        self.summary_tool = ResumeSummaryTool()

    def process_job_description(self, job_description, min_score=None):

        if min_score is None:
            min_score = MIN_MATCH_SCORE

        resumes = self.search_tool.search_resumes(job_description)

        if len(resumes) == 0:
            return []

        final_results = []

        for resume in resumes:

            ranking = self.ranking_tool.rank_resume(
                job_description, resume["content"]
            )

            match_score = extract_match_score(ranking)

            if match_score < min_score:
                continue

            summary = self.summary_tool.summarize_resume(
                resume["content"]
            )

            final_results.append({
                "filename": resume["filename"],
                "match_score": match_score,
                "ranking": ranking,
                "summary": summary
            })

        final_results.sort(key=lambda r: r["match_score"], reverse=True)

        return final_results
