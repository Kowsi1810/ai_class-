from agents import RecruitmentAgent

agent = RecruitmentAgent()

job_description = """
Python Developer

FastAPI

Docker

AWS

3+ Years Experience
"""

results = agent.process_job_description(job_description)

for candidate in results:
    print("=" * 80)
    print("Resume :", candidate["filename"])
    print()
    print(candidate["ranking"])
    print()
    print(candidate["summary"])