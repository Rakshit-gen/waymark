# Waymark

Teams lose the reasoning behind decisions. It lives in Slack threads, PR comments and people's heads, and it
leaves when they do. Waymark takes pasted text (a meeting note, a thread excerpt, a design doc snippet), pulls
out the decisions, and keeps a record you can question later.

What it does with each source:

1. The extractor reads the text and returns decision-shaped statements: a claim, the rationale, the
   systems it mentions, and a confidence from 0 to 1.
2. The contradiction checker compares each new statement with earlier ones that mention the same entity and
   writes up any conflict.
3. The staleness checker flags statements that mention an entity you have marked retired in the registry.
4. The synthesizer answers "why is X this way" from stored statements found with SQLite full text search. It
   cites the statements it used and says so when the record is contested.

The pipeline lives in `backend/orchestrator.py`. Route handlers only call into it.

## Layout

    backend/            FastAPI app, SQLite access (stdlib sqlite3), agents, tests
    backend/agents/     extractor, contradiction, staleness, synthesizer
    frontend/           Vite, React, TypeScript, hand-written CSS
    scripts/smoke_test.py   runs the pipeline once against the real model API

The staleness check is a plain lookup against the registry, so it does not call the model.

## Run the backend

Needs Python 3.10 or newer with SQLite FTS5 and JSON support (standard in current builds).

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r backend/requirements.txt
    export GROQ_API_KEY=your-key
    python -m uvicorn backend.main:app --port 8000

The database file is created at `backend/waymark.db`. Set `WAYMARK_DB` to put it somewhere else. Without a
key, `POST /sources` and `GET /ask` return 503 and everything else still works.

Endpoints:

    POST /sources         {"label": "...", "raw_text": "..."}  run the pipeline
    GET  /statements      statements with contradictions and staleness flags
    GET  /contradictions  contradictions with both claims
    POST /entities        {"name": "...", "status": "active" | "retired"}
    GET  /entities
    GET  /ask?q=...       cited answer

## Run the frontend

Needs Node 20 or newer.

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173. The frontend talks to http://127.0.0.1:8000 by default. Set `VITE_API_BASE` to
change that. `npm run build` type-checks and produces `frontend/dist`.

## Tests

    source .venv/bin/activate
    python -m pytest backend

Every agent takes the model client as an argument, and the tests pass a scripted fake instead of a real one.
`backend/tests/test_orchestrator.py` runs the whole pipeline that way and checks the rows that land in the
database. `backend/tests/test_api.py` does the same over HTTP.

To try the real model once (uses your Groq quota):

    python scripts/smoke_test.py

## Design notes

The interface is a trail log. Cool survey paper, dark green ink, a condensed sign-painter face for headings, a
serif for reading and a monospace for timestamps. Three painted blaze colors carry meaning and nothing else:
blue for the current page and citations, red for a contradiction, yellow for a stale reference.
