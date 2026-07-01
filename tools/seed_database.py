import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from feedback_app.config import get_settings
from feedback_app.database import SessionLocal, init_db
from feedback_app.embeddings import SentenceTransformerEmbedder, TfidfEmbedder
from feedback_app.models import Ticket
from feedback_app.pipeline import rebuild_clusters, rebuild_weekly_report
from feedback_app.schemas import TicketInput
from feedback_app.service import enqueue_ticket, process_job


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/generated/tickets_demo_runtime.csv")
    )
    parser.add_argument("--embedding", choices=["tfidf", "bge"], default="tfidf")
    parser.add_argument("--threshold", type=float)
    args = parser.parse_args()
    settings = get_settings()
    init_db()
    rows = load_rows(args.csv)
    with SessionLocal() as db:
        for row in rows:
            existing = db.scalar(select(Ticket).where(Ticket.external_id == row["ticket_id"]))
            if existing:
                continue
            ticket, job = enqueue_ticket(
                db,
                settings,
                TicketInput(
                    ticket_id=row["ticket_id"],
                    user_type=row["user_type"],
                    channel=row["channel"],
                    message=row["message"],
                    created_at=row["created_at"],
                    current_status=row["current_status"],
                ),
                session_id=None,
                source="synthetic_seed",
            )
            process_job(db, settings, job)
            print(f"seeded {ticket.external_id}")

        if args.embedding == "bge":
            embedder = SentenceTransformerEmbedder(settings.embedding_model)
        else:
            embedder = TfidfEmbedder()
        threshold = args.threshold
        if threshold is None:
            evaluation = Path("artifacts/evaluation/evaluation.json")
            if evaluation.exists():
                payload = json.loads(evaluation.read_text(encoding="utf-8"))
                threshold = payload["clustering"]["frozen_threshold"]
            else:
                threshold = 0.80
        clusters = rebuild_clusters(db, embedder, threshold)
        as_of = max(datetime.fromisoformat(row["created_at"]) for row in rows)
        report = rebuild_weekly_report(db, as_of=as_of)
        print(
            f"complete tickets={len(rows)} clusters={len(clusters)} "
            f"week_start={report.week_start.isoformat()} threshold={threshold}"
        )


if __name__ == "__main__":
    main()

