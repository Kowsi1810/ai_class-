# ===========================================
# config.py
# Central configuration file
# ===========================================

import os

# Get the current directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root folder
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Folder containing uploaded resumes
RESUME_FOLDER = os.path.join(PROJECT_ROOT, "resumes")

# ChromaDB storage location
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# ChromaDB collection name
COLLECTION_NAME = "resume_collection"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Number of resumes to retrieve
TOP_K = 5

# Minimum match score (0-100) a candidate must have to be
# included in the final results. Candidates the LLM scores
# below this are considered irrelevant and filtered out.
MIN_MATCH_SCORE = 50

# Supported resume extensions
SUPPORTED_FILES = [".pdf"]

print("========== CONFIG ==========")
print("Resume Folder :", RESUME_FOLDER)
print("Chroma DB     :", CHROMA_DB_PATH)
print("Collection    :", COLLECTION_NAME)
print("============================")