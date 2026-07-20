# Multi-User Conversational Memory Chatbot

LangChain + Groq + FastAPI backend, with a plain HTML/CSS/JS frontend, demonstrating
per-user, per-session conversational memory backed by a JSON file — no database,
no login.

## How identity works

- **`user_id`**: generated once in the browser with `crypto.randomUUID()` and saved
  to `localStorage`. The same browser reuses it forever; a different browser/tab-in-
  incognito gets a different id, simulating a different "user."
- **`session_id`**: generated with `crypto.randomUUID()` every time **New chat** is
  clicked. One user can have many sessions; each has its own independent memory.

## Project layout

```
backend/
  main.py               FastAPI app + routes
  chatbot.py             LangChain + ChatGroq logic
  memory.py               JSON storage layer (swap-out point for a future DB)
  schemas.py                Pydantic request/response models
  config.py                   Env/config loading
  requirements.txt
  .env.example                 Copy to .env and add your Groq key
  memory/conversations.json     Data file (starts as {})
frontend/
  index.html
  style.css
  script.js
```

## 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then edit .env and set GROQ_API_KEY=your_real_key
# (get one free at https://console.groq.com)

uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` — interactive docs at
`http://localhost:8000/docs`.

## 2. Frontend setup

The frontend is static files — no build step. Simplest option, open a second
terminal:

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500` in your browser. (Opening `index.html`
directly by double-clicking also works in most browsers, since it only talks
to the backend over `fetch`.)

If your backend runs on a different host/port, update `API_BASE_URL` at the
top of `frontend/script.js`.

## 3. Try it

1. Open the app — a `user_id` is silently created and stored in `localStorage`.
2. Click **New chat**, say "My name is Rahul", then ask "What is my name?" —
   it remembers, because it's the same session.
3. Click **New chat** again and ask "Who am I?" — it won't know, because this
   is a brand-new, independent session.
4. Open the app in a private/incognito window — that's a different `user_id`
   with its own separate list of chats.

## Upgrading storage later

Every read/write to `conversations.json` goes through `backend/memory.py`.
To move to SQLite/Postgres/MongoDB/Redis, reimplement the functions in that
one file (`get_sessions`, `get_history`, `append_message`, `create_session`,
`delete_session`) against your database — `main.py`, `chatbot.py`, and the
entire frontend stay untouched.
