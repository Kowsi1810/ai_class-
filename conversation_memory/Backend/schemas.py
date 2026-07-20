"""
schemas.py
----------
Pydantic models describing the shape of every request and response the
API accepts/returns. FastAPI uses these for validation, serialization,
and auto-generated docs (/docs).

Connects to:
- main.py -> every route uses one of these models for its request body
  or response_model.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body for POST /chat"""
    user_id: str = Field(..., description="UUID generated client-side and stored in localStorage")
    session_id: str = Field(..., description="UUID identifying a single conversation")
    message: str = Field(..., min_length=1, description="The user's message text")


class ChatResponse(BaseModel):
    """Response for POST /chat"""
    response: str


class Message(BaseModel):
    """A single turn in a conversation, as stored in conversations.json"""
    role: Literal["user", "assistant"]
    content: str


class NewSessionResponse(BaseModel):
    """Response for POST /new-session"""
    session_id: str


class DeleteResponse(BaseModel):
    """Response for DELETE /chat/{user_id}/{session_id}"""
    status: str
    user_id: str
    session_id: str
