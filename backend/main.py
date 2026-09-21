"""FastAPI app. Route handlers stay thin, all pipeline logic lives in
backend/orchestrator.py."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import db, orchestrator
from backend.llm_client import LLMClient

@asynccontextmanager
async def lifespan(_app):
    conn = db.get_connection()
    db.init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Waymark", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    return db.get_connection()


def get_llm_client() -> LLMClient:
    try:
        return LLMClient()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


class SourceIn(BaseModel):
    label: str
    raw_text: str


class EntityIn(BaseModel):
    name: str
    status: str


@app.post("/sources")
def add_source(body: SourceIn, client=Depends(get_llm_client)):
    conn = get_conn()
    try:
        statements = orchestrator.add_source(conn, client, body.label, body.raw_text)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=502, detail="The model returned output Waymark could not read. Try again.")
    finally:
        conn.close()
    return {"statements": statements}


@app.get("/statements")
def list_statements():
    conn = get_conn()
    try:
        rows = db.all_statements(conn)
        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "source_id": row["source_id"],
                    "source_label": row["source_label"],
                    "claim": row["claim"],
                    "rationale": row["rationale"],
                    "referenced_entities": json.loads(row["referenced_entities"]),
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "contradictions": [dict(c) for c in db.contradictions_for_statement(conn, row["id"])],
                    "staleness_flags": [dict(f) for f in db.staleness_for_statement(conn, row["id"])],
                }
            )
        return {"statements": result}
    finally:
        conn.close()


@app.get("/contradictions")
def list_contradictions():
    conn = get_conn()
    try:
        rows = db.all_contradictions(conn)
        result = []
        for row in rows:
            a = db.get_statement(conn, row["statement_a_id"])
            b = db.get_statement(conn, row["statement_b_id"])
            result.append(
                {
                    "id": row["id"],
                    "statement_a_id": row["statement_a_id"],
                    "statement_a_claim": a["claim"] if a else None,
                    "statement_b_id": row["statement_b_id"],
                    "statement_b_claim": b["claim"] if b else None,
                    "explanation": row["explanation"],
                    "created_at": row["created_at"],
                }
            )
        return {"contradictions": result}
    finally:
        conn.close()


@app.post("/entities")
def add_entity(body: EntityIn):
    if body.status not in ("active", "retired"):
        raise HTTPException(status_code=400, detail="status must be 'active' or 'retired'")
    conn = get_conn()
    try:
        entity_id = db.upsert_entity(conn, body.name, body.status)
        return {"id": entity_id, "name": body.name, "status": body.status}
    finally:
        conn.close()


@app.get("/entities")
def list_entities():
    conn = get_conn()
    try:
        return {"entities": [dict(row) for row in db.all_entities(conn)]}
    finally:
        conn.close()


@app.get("/ask")
def ask(q: str, client=Depends(get_llm_client)):
    conn = get_conn()
    try:
        return orchestrator.ask(conn, client, q)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=502, detail="The model returned output Waymark could not read. Try again.")
    finally:
        conn.close()
