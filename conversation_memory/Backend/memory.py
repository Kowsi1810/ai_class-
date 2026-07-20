"""
memory.py
---------
All persistence logic lives here, isolated from the rest of the app.

Storage shape (backend/memory/conversations.json):

{
  "<user_id>": {
      "<session_id>": [
          {"user_id": "<user_id>", "session_id": "<session_id>", "role": "user", "content": "...", "timestamp": "2026-07-18T19:35:18.123456"},
          {"user_id": "<user_id>", "session_id": "<session_id>", "role": "assistant", "content": "...", "timestamp": "2026-07-18T19:35:19.987654"}
      ],
      ...
  },
  ...
}

Each message now records the wall-clock time it was logged (timestamp),
plus its own user_id and session_id explicitly -- in addition to already
being nested under those same keys. The "<session_id>" key (and the
matching "session_id" field inside each message) is the identifier that
ties every message in a chat to the same conversation for that user --
i.e. same user_id + same session_id = same ongoing chat.

Why this file exists:
- Keeps main.py / chatbot.py free of file I/O details.
- Gives us a single seam to swap for SQLite/Postgres/Redis later: every
  function here can be reimplemented against a DB without changing its
  signature, so main.py and chatbot.py never need to change.

Connects to:
- main.py    -> calls these functions from every route.
- chatbot.py -> receives the plain list-of-dicts history returned here and
  converts it into LangChain message objects.
"""

import json
import os
import uuid
from datetime import datetime
from threading import Lock
from typing import Dict, List

from config import MEMORY_DIR, MEMORY_FILE_PATH

# A simple in-process lock to avoid two concurrent requests corrupting the
# JSON file with interleaved writes. Fine for a demo/single-process app;
# a real DB would handle this for us.
_file_lock = Lock()


def _ensure_storage_exists() -> None:
    """Create the memory/ directory and an empty conversations.json if missing."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    if not os.path.exists(MEMORY_FILE_PATH):
        with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _read_all() -> Dict[str, Dict[str, List[dict]]]:
    """Load the entire conversations.json into memory as a dict."""
    _ensure_storage_exists()
    with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # File exists but is empty/corrupt -> treat as empty store.
            return {}


def _write_all(data: Dict[str, Dict[str, List[dict]]]) -> None:
    """Persist the entire store back to conversations.json."""
    _ensure_storage_exists()
    with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_sessions(user_id: str) -> List[str]:
    """Return all session_ids that belong to a given user_id."""
    with _file_lock:
        data = _read_all()
    return list(data.get(user_id, {}).keys())


def get_history(user_id: str, session_id: str) -> List[dict]:
    """Return the message list for one user's one session (empty list if new)."""
    with _file_lock:
        data = _read_all()
    return data.get(user_id, {}).get(session_id, [])


def append_message(user_id: str, session_id: str, role: str, content: str) -> None:
    """
    Append a single message to a user's session, auto-creating the user
    and/or session if they don't exist yet.

    Every message is stamped with the moment it was logged (ISO 8601), and
    also carries its own user_id/session_id explicitly (in addition to
    being nested under those same keys), so each entry is self-describing
    on its own -- useful for logging, exporting, or a future DB migration
    where rows are flattened out of the nested structure.
    """
    with _file_lock:
        data = _read_all()
        data.setdefault(user_id, {})
        data[user_id].setdefault(session_id, [])
        data[user_id][session_id].append(
            {
                "user_id": user_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        _write_all(data)


def create_session(user_id: str) -> str:
    """
    Create a brand-new empty session for a user and return its id.
    Used by POST /new-session. (The frontend may also generate ids itself
    with crypto.randomUUID(); this endpoint exists for symmetry / server
    trust if the frontend wants the backend to be the source of truth.)
    """
    session_id = str(uuid.uuid4())
    with _file_lock:
        data = _read_all()
        data.setdefault(user_id, {})
        data[user_id].setdefault(session_id, [])
        _write_all(data)
    return session_id


def delete_session(user_id: str, session_id: str) -> bool:
    """Delete one session for one user. Returns True if something was deleted."""
    with _file_lock:
        data = _read_all()
        if user_id in data and session_id in data[user_id]:
            del data[user_id][session_id]
            _write_all(data)
            return True
    return False