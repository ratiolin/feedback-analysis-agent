import logging
import time

from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal, init_db
from .models import AnalysisJob
from .service import process_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feedback-worker")


def run_once() -> bool:
    settings = get_settings()
    with SessionLocal() as db:
        job = db.scalar(
            select(AnalysisJob)
            .where(AnalysisJob.status == "queued")
            .order_by(AnalysisJob.created_at)
            .limit(1)
        )
        if job is None:
            return False
        try:
            process_job(db, settings, job)
        except Exception:
            logger.exception("analysis job %s failed", job.id)
        return True


def main() -> None:
    init_db()
    logger.info("feedback worker started")
    while True:
        if not run_once():
            time.sleep(1)


if __name__ == "__main__":
    main()

