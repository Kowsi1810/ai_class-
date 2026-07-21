# Recruitment Agent — Frontend

A React (Vite) UI for the FastAPI recruitment agent in `../Backend`.

## Setup

```bash
cd Frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` and expects the backend at
`http://localhost:8000` by default (CORS is already open on the
backend). To point at a different backend URL, create a `.env` file:

```
VITE_API_BASE=http://localhost:8000
```

## What it does

- Paste a job description and set a minimum match score (0–100).
- Calls `POST /search` on the backend.
- Renders each returned candidate as a card: name, filename, a
  rotated "match stamp" with the score, the LLM's plain-language
  summary, and a collapsible "reviewer notes" section with the
  reasoning, strengths, and watch-outs pulled out of the ranking text.
- Candidates below the minimum score never come back from the
  backend at all (filtered server-side), so the list only ever
  shows genuine matches, best first.

## Build for production

```bash
npm run build
```

Outputs static files to `dist/`, which you can serve with any static
host (or point FastAPI at it with `StaticFiles` if you want a single
deployable app).
