from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from feedback_app.config import Settings
from feedback_app.database import Base
from feedback_app.models import AnalysisJob
from feedback_app.schemas import TicketInput
from feedback_app.service import create_demo_session, enqueue_ticket, process_job


def make_db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_ticket_job_can_be_processed_with_transparent_demo_fallback() -> None:
    db = make_db()
    settings = Settings(database_url="sqlite://", allow_demo_analyzer=True)
    demo_session = create_demo_session(db, settings)
    ticket, job = enqueue_ticket(
        db,
        settings,
        TicketInput(
            ticket_id="T001",
            message="我们团队无法收到任务到期通知，已经联系两次。",
            created_at=datetime.now(UTC),
        ),
        demo_session.id,
    )
    analysis = process_job(db, settings, job)
    assert analysis.ticket_id == ticket.id
    assert analysis.analysis_source == "demo_rules"
    assert db.get(AnalysisJob, job.id).status == "completed"

