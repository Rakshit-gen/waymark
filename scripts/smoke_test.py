"""Runs the real pipeline against the live model API once, on a short
example. Requires ANTHROPIC_API_KEY to be set. Run from the repo root:

    python scripts/smoke_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import db, orchestrator
from backend.llm_client import LLMClient

EXAMPLE_TEXT = """
Meeting notes, infra sync:
We decided to run our background jobs on Postgres-backed queues instead of
standing up a separate message broker, because the team already operates
Postgres and did not want to take on Kafka's operational cost for our
current volume. We also agreed to retire the old Jenkins pipeline in favor
of GitHub Actions, since Jenkins was the one thing nobody on the team could
still administer confidently.
"""


def main():
    conn = db.get_connection(":memory:")
    db.init_db(conn)
    client = LLMClient()

    print("Adding source...")
    statements = orchestrator.add_source(conn, client, "infra sync notes", EXAMPLE_TEXT)
    print(f"Extracted {len(statements)} statement(s):")
    for s in statements:
        print(f"  - {s['claim']} (confidence {s['confidence']})")

    print("\nAsking a question...")
    result = orchestrator.ask(conn, client, "why did we move off Jenkins")
    print(f"Answer: {result['answer']}")
    print(f"Cited ids: {result['cited_ids']}, contested: {result['contested']}")


if __name__ == "__main__":
    main()
