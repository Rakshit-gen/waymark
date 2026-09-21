"""FastAPI app. Route handlers stay thin, all pipeline logic lives in
backend/orchestrator.py."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import db, orchestrator
from backend.llm_client import LLMClient

app = FastAPI(title="Waymark")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    conn = db.get_connection()
    db.init_db(conn)
    conn.close()


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


@app.post("/sources")
def add_source(body: SourceIn):
    conn = get_conn()
    client = get_llm_client()
    try:
        statements = orchestrator.add_source(conn, client, body.label, body.raw_text)
    finally:
        conn.close()
    return {"statements": statements}
