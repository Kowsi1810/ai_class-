"""
config.py
---------
Centralized configuration for the backend.

Loads environment variables from a local .env file (never hardcode secrets)
and exposes them as simple constants that the rest of the app can import.

Connects to:
- chatbot.py -> uses GROQ_API_KEY and GROQ_MODEL to build the ChatGroq client.
- main.py    -> uses MEMORY_FILE_PATH indirectly via memory.py, and CORS settings.
"""

import os
from dotenv import load_dotenv

# Load variables from backend/.env into the process environment.
load_dotenv()

# ---- Groq / LangChain settings -------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    # We don't crash on import so the app can still start (e.g. during setup),
    # but chatbot.py will raise a clearer error the moment it's actually used.
    print("WARNING: GROQ_API_KEY is not set. Add it to backend/.env before chatting.")

# ---- Storage settings ------------------------------------------------------------
# Kept as a single JSON file for now. Swap this out for a DB-backed
# implementation later without touching main.py or the frontend.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
MEMORY_FILE_PATH = os.path.join(MEMORY_DIR, "conversations.json")

# ---- CORS settings ----------------------------------------------------------------
# Wide open for local development since the frontend is plain static files
# opened via a dev server / file path with no fixed origin.
ALLOWED_ORIGINS = ["*"]
