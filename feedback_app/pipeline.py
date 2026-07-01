from collections import Counter, defaultdict
from datetime import UTC, datetime

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .clustering import threshold_clusters
from .embeddings import Embedder
from .models import (
    Analysis,
    ClusterMember,
    IssueCluster,
    SOPCandidate,
    Ticket,
    WeeklyReport,
)
from .reports import build_weekly_report, report_to_markdown, trend_for_dates
from .sop import build_sop_candidate

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
OWNER_ACTIONS = {
    "customer_success": "客户成功确认配置，并更新一线排查话术",
    "implementation_support": "实施顾问核对组织和权限配置",
    "technical_support": "技术支持复现接口调用并核对请求日志",
    "qa_triage": "QA 复现数据路径并记录最小复现步骤",
    "engineering_triage": "工程团队核查性能指标和错误日志",
    "product_ops": "产品运营汇总需求并确认提示或流程改进",
}


def rebuild_clusters(db: Session, embedder: Embedder, threshold: float) -> list[IssueCluster]:
    rows = db.execute(
        select(Ticket, Analysis)
        .join(Analysis, Analysis.ticket_id == Ticket.id)
        .where(Ticket.session_id.is_(None))
        .order_by(Ticket.external_id)
    ).all()
    if not rows:
        return []
    texts = [analysis.payload["summary"] for _, analysis in rows]
    vectors = np.asarray(embedder.encode(texts), dtype=float)
    labels = threshold_clusters(vectors, threshold)
    grouped: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        grouped[label].append(index)

    db.execute(delete(SOPCandidate))
    db.execute(delete(ClusterMember))
    db.execute(delete(IssueCluster))
    db.flush()
    clusters: list[IssueCluster] = []
    for indexes in grouped.values():
        group = [rows[index] for index in indexes]
        analyses = [analysis for _, analysis in group]
        tickets = [ticket for ticket, _ in group]
        owners = Counter(analysis.suggested_owner for analysis in analyses)
        owner = owners.most_common(1)[0][0]
        severity = max(
            (analysis.severity for analysis in analyses), key=lambda item: SEVERITY_ORDER[item]
        )
        title = min((analysis.payload["summary"] for analysis in analyses), key=len)[:80]
        representatives = [ticket.external_id for ticket in tickets[:3]]
        evidence = [
            {
                "ticket_id": ticket.external_id,
                "quote": analysis.payload["evidence_spans"][0]["quote"],
            }
            for ticket, analysis in group[:3]
            if analysis.payload.get("evidence_spans")
        ]
        hypotheses = [
            analysis.payload.get("root_cause_hypothesis")
            for analysis in analyses
            if analysis.payload.get("root_cause_hypothesis")
        ]
        centroid = vectors[indexes].mean(axis=0).tolist()
        cluster = IssueCluster(
            title=title,
            summary=f"{len(group)} 条相似工单，建议责任方为 {owner}",
            member_count=len(group),
            severity=severity,
            trend=trend_for_dates([ticket.created_at for ticket in tickets], datetime.now(UTC)),
            suggested_owner=owner,
            centroid=centroid,
            representative_ticket_ids=representatives,
            evidence=evidence,
        )
        db.add(cluster)
        db.flush()
        for ticket in tickets:
            db.add(ClusterMember(cluster_id=cluster.id, ticket_id=ticket.id))
        cluster_payload = {
            "title": cluster.title,
            "member_count": cluster.member_count,
            "trend": cluster.trend,
            "severity": cluster.severity,
            "representative_ticket_ids": representatives,
        }
        candidate = build_sop_candidate(cluster_payload)
        if candidate:
            candidate["pending_cause"] = hypotheses[0] if hypotheses else None
            candidate["recommended_action"] = OWNER_ACTIONS.get(owner, "人工确认责任方")
            db.add(
                SOPCandidate(
                    cluster_id=cluster.id,
                    title=candidate["title"],
                    payload=candidate,
                )
            )
        clusters.append(cluster)
    db.commit()
    return clusters


def rebuild_weekly_report(db: Session, as_of: datetime | None = None) -> WeeklyReport:
    as_of = as_of or datetime.now(UTC)
    ticket_rows = db.execute(
        select(Ticket, Analysis)
        .join(Analysis, Analysis.ticket_id == Ticket.id)
        .where(Ticket.session_id.is_(None))
    ).all()
    cluster_rows = db.scalars(select(IssueCluster)).all()
    tickets = [
        {"created_at": ticket.created_at, "severity": analysis.severity}
        for ticket, analysis in ticket_rows
    ]
    clusters = [
        {
            "title": cluster.title,
            "member_count": cluster.member_count,
            "representative_ticket_ids": cluster.representative_ticket_ids,
            "root_cause_hypothesis": None,
            "recommended_action": OWNER_ACTIONS.get(cluster.suggested_owner),
        }
        for cluster in cluster_rows
    ]
    payload = build_weekly_report(tickets, clusters, as_of)
    week_start = as_of.replace(hour=0, minute=0, second=0, microsecond=0)
    report = db.scalar(select(WeeklyReport).where(WeeklyReport.week_start == week_start))
    if report is None:
        report = WeeklyReport(
            week_start=week_start,
            payload=payload,
            markdown=report_to_markdown(payload),
        )
        db.add(report)
    else:
        report.payload = payload
        report.markdown = report_to_markdown(payload)
    db.commit()
    db.refresh(report)
    return report
