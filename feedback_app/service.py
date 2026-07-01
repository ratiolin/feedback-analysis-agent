import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .analysis import finalize_analysis
from .analyzers import AnalyzerError, DemoAnalyzer, DifyAnalyzer
from .config import Settings
from .models import Analysis, AnalysisJob, DemoSession, Ticket, utc_now
from .privacy import sanitize_message
from .schemas import TicketInput


def input_hash(message: str, workflow_version: str) -> str:
    normalized = " ".join(message.split()).casefold()
    return hashlib.sha256(f"{workflow_version}\0{normalized}".encode()).hexdigest()


def create_demo_session(db: Session, settings: Settings, ip_hash: str = "") -> DemoSession:
    session = DemoSession(
        ip_hash=ip_hash,
        expires_at=datetime.now(UTC) + timedelta(hours=settings.demo_session_ttl_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def require_active_session(db: Session, session_id: str) -> DemoSession:
    demo_session = db.get(DemoSession, session_id)
    if demo_session is None or demo_session.expires_at < datetime.now(UTC):
        raise ValueError("demo_session_expired")
    return demo_session


def count_session_tickets_today(db: Session, session_id: str) -> int:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.session_id == session_id,
            Ticket.ingested_at >= start,
            Ticket.source == "live",
        )
    ) or 0


def enqueue_ticket(
    db: Session,
    settings: Settings,
    payload: TicketInput,
    session_id: str | None,
    source: str = "live",
) -> tuple[Ticket, AnalysisJob]:
    sanitized = sanitize_message(payload.message)
    ticket = Ticket(
        external_id=payload.ticket_id,
        session_id=session_id,
        user_type=payload.user_type,
        channel=payload.channel,
        message=sanitized,
        created_at=payload.created_at,
        current_status=payload.current_status,
        input_hash=input_hash(sanitized, settings.workflow_version),
        source=source,
    )
    db.add(ticket)
    db.flush()
    job = AnalysisJob(ticket_id=ticket.id)
    db.add(job)
    db.commit()
    db.refresh(ticket)
    db.refresh(job)
    return ticket, job


def process_job(db: Session, settings: Settings, job: AnalysisJob) -> Analysis:
    ticket = db.get(Ticket, job.ticket_id)
    if ticket is None:
        raise ValueError("ticket_not_found")
    existing = db.scalar(select(Analysis).where(Analysis.ticket_id == ticket.id))
    if existing:
        job.status = "completed"
        job.updated_at = utc_now()
        db.commit()
        return existing

    job.status = "processing"
    job.attempts += 1
    job.updated_at = utc_now()
    db.commit()
    ticket_payload = TicketInput(
        ticket_id=ticket.external_id,
        user_type=ticket.user_type,
        channel=ticket.channel,
        message=ticket.message,
        created_at=ticket.created_at,
        current_status=ticket.current_status,
    )
    source = "dify"
    try:
        raw = DifyAnalyzer(settings).analyze(ticket_payload)
    except Exception as exc:
        if not settings.allow_demo_analyzer:
            job.status = "queued" if job.attempts < 3 else "failed"
            job.last_error = f"{type(exc).__name__}: {exc}"[:1000]
            job.updated_at = utc_now()
            db.commit()
            raise AnalyzerError(job.last_error) from exc
        raw = DemoAnalyzer().analyze(ticket_payload)
        source = "demo_rules"
    final = finalize_analysis(ticket.message, raw, settings.workflow_version, source)
    analysis = Analysis(
        ticket_id=ticket.id,
        payload=final.model_dump(mode="json"),
        problem_type=final.problem_type.value,
        product_area=final.product_area.value,
        suggested_owner=final.suggested_owner.value,
        severity=final.severity.value,
        needs_escalation=final.needs_escalation,
        review_status=final.review_status.value,
        workflow_version=final.workflow_version,
        analysis_source=final.analysis_source,
    )
    db.add(analysis)
    job.status = "completed" if final.review_status.value != "needs_review" else "needs_review"
    job.last_error = None
    job.updated_at = utc_now()
    db.commit()
    db.refresh(analysis)
    return analysis
