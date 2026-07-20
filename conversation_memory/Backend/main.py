"""
main.py
-------
FastAPI application entry point. Defines all REST endpoints and wires
together memory.py (storage) and chatbot.py (LangChain + Groq).

Run with:
    uvicorn main:app --reload --port 8000

Connects to:
- schemas.py -> request/response models for every route.
- memory.py  -> reading/writing conversations.json.
- chatbot.py -> generating LLM responses.
- frontend/script.js -> calls these endpoints via fetch().
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import chatbot
import memory
from config import ALLOWED_ORIGINS
from schemas import (
    ChatRequest,
    ChatResponse,
    NewSessionResponse,
    DeleteResponse,
)

app = FastAPI(
    title="Multi-User Conversational Memory Chatbot",
    description="LangChain + Groq powered chatbot with per-user, per-session memory.",
    version="1.0.0",
)

# Allow the static frontend (served from a different origin/port, or opened
# directly as a file) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Simple health check."""
    return {"status": "ok", "message": "Chatbot backend is running."}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.

    Flow:
    1. Load existing history for (user_id, session_id).
    2. Convert it + the new message into LangChain messages.
    3. Call Groq via LangChain to get a reply.
    4. Persist both the user message and the assistant reply.
    5. Return the assistant reply.
    """
    history = memory.get_history(request.user_id, request.session_id)

    try:
        ai_response = chatbot.generate_response(history, request.message)
    except RuntimeError as e:
        # e.g. missing API key
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    # Persist the exchange only after a successful LLM call, so a failed
    # call doesn't leave a "dangling" user message with no reply.
    memory.append_message(request.user_id, request.session_id, "user", request.message)
    memory.append_message(request.user_id, request.session_id, "assistant", ai_response)

    return ChatResponse(response=ai_response)


@app.get("/sessions/{user_id}")
def list_sessions(user_id: str):
    """Return all session_ids that belong to a given user."""
    return memory.get_sessions(user_id)


@app.get("/chat-history/{user_id}/{session_id}")
def chat_history(user_id: str, session_id: str):
    """Return the full message list for one specific session."""
    return memory.get_history(user_id, session_id)


@app.post("/new-session", response_model=NewSessionResponse)
def new_session(user_id: str):
    """
    Create a brand-new empty session for a user and return its id.
    user_id is passed as a query param, e.g. POST /new-session?user_id=abc
    """
    session_id = memory.create_session(user_id)
    return NewSessionResponse(session_id=session_id)


@app.delete("/chat/{user_id}/{session_id}", response_model=DeleteResponse)
def delete_chat(user_id: str, session_id: str):
    """Delete a single conversation, leaving other sessions untouched."""
    deleted = memory.delete_session(user_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return DeleteResponse(status="deleted", user_id=user_id, session_id=session_id)
