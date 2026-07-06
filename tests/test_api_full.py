from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from feedback_app.config import Settings, get_settings
from feedback_app.database import Base, get_db
from feedback_app.main import app


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_health():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url="sqlite://", allow_demo_analyzer=True,
    )
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    app.dependency_overrides.clear()
    db.close()


def test_metrics():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: Settings(database_url="sqlite://")
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    app.dependency_overrides.clear()
    db.close()


def test_create_demo_session():
    db = make_db()
    s = Settings(database_url="sqlite://", allow_demo_analyzer=True)
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: s
    client = TestClient(app)
    r = client.post("/v1/demo/sessions", json={})
    assert r.status_code == 201
    app.dependency_overrides.clear()
    db.close()


def test_get_job_404():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: Settings(database_url="sqlite://")
    client = TestClient(app)
    r = client.get("/v1/jobs/nonexistent")
    assert r.status_code == 404
    app.dependency_overrides.clear()
    db.close()


def test_list_tickets():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: Settings(database_url="sqlite://")
    client = TestClient(app)
    r = client.get("/v1/tickets")
    assert r.status_code == 200
    app.dependency_overrides.clear()
    db.close()


def test_list_clusters():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: Settings(database_url="sqlite://")
    client = TestClient(app)
    r = client.get("/v1/clusters")
    assert r.status_code == 200
    app.dependency_overrides.clear()
    db.close()