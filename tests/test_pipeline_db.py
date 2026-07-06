from datetime import UTC, datetime

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from feedback_app.config import Settings
from feedback_app.database import Base
from feedback_app.models import Analysis, ClusterMember, IssueCluster, Ticket
from feedback_app.pipeline import _build_single_cluster, _truncate_cluster_tables


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _ticket(db, eid, msg="test"):
    t = Ticket(id=eid, external_id=eid, message=msg, input_hash=eid,
               created_at=datetime(2025, 1, 1, tzinfo=UTC))
    db.add(t)
    db.flush()
    return t


def _analysis(db, tid, summary, owner="ops", severity="medium",
              area="General", ptype="Bug", review="pending"):
    a = Analysis(ticket_id=tid, payload={"summary": summary},
                 problem_type=ptype, product_area=area,
                 suggested_owner=owner, severity=severity,
                 review_status=review, workflow_version="v1",
                 analysis_source="test")
    db.add(a)
    db.flush()
    return a


def test_build_single_cluster_creates_cluster_and_members():
    db = make_db()
    s = Settings(cluster_block_by_problem_type=False)
    t1 = _ticket(db, "T1")
    t2 = _ticket(db, "T2")
    a1 = _analysis(db, t1.id, "Login timeout")
    a2 = _analysis(db, t2.id, "Login freeze")
    rows = [(t1, a1), (t2, a2)]
    vecs = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float)
    _build_single_cluster(db, rows, vecs, [0, 1], s)
    db.commit()
    c = db.query(IssueCluster).first()
    assert c is not None
    assert c.member_count == 2
    assert db.query(ClusterMember).count() == 2
    db.close()


def test_truncate_cluster_clears_all():
    db = make_db()
    t = _ticket(db, "T1")
    a = _analysis(db, t.id, "test")
    rows = [(t, a)]
    _build_single_cluster(db, rows, np.array([[1.0, 2.0]], dtype=float), [0], Settings())
    db.commit()
    assert db.query(IssueCluster).count() == 1
    _truncate_cluster_tables(db)
    assert db.query(IssueCluster).count() == 0
    db.close()