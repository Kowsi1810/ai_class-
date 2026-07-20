"""
chatbot.py
----------
All LangChain / Groq logic lives here, isolated from the web layer.

Responsibilities:
- Build a ChatGroq LLM client.
- Convert plain-dict conversation history (as stored in JSON) into
  LangChain message objects (HumanMessage / AIMessage).
- Build a ChatPromptTemplate that includes a system prompt + full history
  + the new user message.
- Run the prompt through the LLM using LCEL (prompt | llm) and return the
  text response.

Connects to:
- config.py -> GROQ_API_KEY / GROQ_MODEL.
- memory.py -> main.py fetches history via memory.get_history() and passes
  the raw list of dicts into build_messages_from_history() below.
- main.py   -> calls generate_response() with the full history + new message.
"""

from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = (
    "You are a helpful, friendly AI assistant. Use the conversation history "
    "provided to you to remember details the user has shared earlier in THIS "
    "conversation (this session only). If the user asks about something that "
    "was never mentioned in this session, say so honestly instead of "
    "guessing or assuming it came from another conversation."
)

# Lazily created singleton so we don't reconnect on every request.
_llm = None


def _get_llm() -> ChatGroq:
    """Return a cached ChatGroq client, creating it on first use."""
    global _llm
    if _llm is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to backend/.env "
                "(see .env.example) before sending chat messages."
            )
        _llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.7,
        )
    return _llm


def build_messages_from_history(history: List[dict]) -> List:
    """
    Convert the JSON-stored history (list of {"role": ..., "content": ...})
    into a list of LangChain message objects, in order.
    """
    messages = []
    for turn in history:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        # Unknown roles are ignored defensively rather than crashing.
    return messages


def generate_response(history: List[dict], new_user_message: str) -> str:
    """
    Given the prior conversation (as plain dicts) and a new user message,
    call the Groq LLM (via LangChain LCEL) and return the assistant's reply
    as a plain string.

    This function does NOT persist anything — main.py is responsible for
    saving both the user message and this returned response via memory.py.
    """
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content=new_user_message),
        ]
    )

    # LCEL: pipe the formatted prompt straight into the LLM.
    chain = prompt | llm

    past_messages = build_messages_from_history(history)
    result = chain.invoke({"history": past_messages})

    return result.content
