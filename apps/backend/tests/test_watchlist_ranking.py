"""
Unit tests for watchlist and ranking API endpoints.

Tests cover:
- POST /watchlist: add stock (success, duplicate 409, max limit 400)
- DELETE /watchlist/{code}: remove stock
- GET /ranking: pagination, sort by score desc, filter by sector

Uses FastAPI TestClient with dependency override for SQLite in-memory DB.
"""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.models.stock import Stock, StockScore
from app.models.user import LoginAttempt, RefreshToken, User
from app.models.watchlist import Watchlist
from app.services.auth_service import login_user, register_user


# ---------------------------------------------------------------------------
# Test DB setup (separate from conftest to avoid session-scope conflicts)
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"

_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_engine)

_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session():
    """Provide a clean DB session for each test."""
    session = _TestingSessionLocal()
    yield session
    session.close()
    # Clean up all tables between tests
    with _engine.begin() as conn:
        conn.execute(Watchlist.__table__.delete())
        conn.execute(StockScore.__table__.delete())
        conn.execute(Stock.__table__.delete())
        conn.execute(RefreshToken.__table__.delete())
        conn.execute(LoginAttempt.__table__.delete())
        conn.execute(User.__table__.delete())


@pytest.fixture
def client(db_session):
    """TestClient with get_db overridden to use the test SQLite DB."""
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def stocks_in_db(db_session: Session):
    """Insert sample stocks into the test DB."""
    stocks = [
        Stock(code="BBCA", name="Bank Central Asia Tbk", sector="Keuangan", is_active=True),
        Stock(code="BBRI", name="Bank Rakyat Indonesia Tbk", sector="Keuangan", is_active=True),
        Stock(code="BMRI", name="Bank Mandiri Tbk", sector="Keuangan", is_active=True),
        Stock(code="TLKM", name="Telkom Indonesia Tbk", sector="Teknologi", is_active=True),
        Stock(code="ASII", name="Astra International Tbk", sector="Industri", is_active=True),
    ]
    for s in stocks:
        db_session.add(s)
    db_session.commit()
    return stocks


@pytest.fixture
def stocks_with_scores(db_session: Session):
    """Insert stocks with scores for ranking tests."""
    stocks_data = [
        ("BBCA", "Bank Central Asia Tbk", "Keuangan", 85.0),
        ("BBRI", "Bank Rakyat Indonesia Tbk", "Keuangan", 78.0),
        ("BMRI", "Bank Mandiri Tbk", "Keuangan", 72.0),
        ("TLKM", "Telkom Indonesia Tbk", "Teknologi", 90.0),
        ("ASII", "Astra International Tbk", "Industri", 65.0),
        ("UNVR", "Unilever Indonesia Tbk", "Konsumer", 60.0),
        ("INDF", "Indofood Sukses Makmur Tbk", "Konsumer", 55.0),
    ]
    now = datetime.now(timezone.utc)
    for code, name, sector, score in stocks_data:
        stock = Stock(code=code, name=name, sector=sector, is_active=True)
        db_session.add(stock)
        db_session.flush()
        db_session.add(StockScore(
            stock_id=stock.id,
            score=score,
            is_partial=False,
            calculated_at=now,
        ))
    db_session.commit()


@pytest.fixture
def auth_user(client, db_session: Session):
    """Register and login a test user, return the access_token."""
    with patch("app.services.auth_service._send_verification_email"):
        register_user(
            db_session,
            email="testuser@example.com",
            password="TestPass123!",
            name="Test User",
        )
    tokens = login_user(db_session, email="testuser@example.com", password="TestPass123!")
    return tokens["access_token"]


# ---------------------------------------------------------------------------
# Watchlist tests
# ---------------------------------------------------------------------------


def test_add_to_watchlist_success(client, stocks_in_db, auth_user):
    """Req 6.2 — POST /watchlist should successfully add a stock."""
    response = client.post(
        "/api/v1/watchlist/",
        json={"code": "BBCA"},
        headers={"Authorization": f"Bearer {auth_user}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "BBCA" in data["message"]


def test_add_to_watchlist_duplicate(client, stocks_in_db, auth_user):
    """Req 6.3 — Adding a stock already in watchlist should return HTTP 409."""
    headers = {"Authorization": f"Bearer {auth_user}"}
    # Add once
    client.post("/api/v1/watchlist/", json={"code": "BBCA"}, headers=headers)
    # Add again — should conflict
    response = client.post("/api/v1/watchlist/", json={"code": "BBCA"}, headers=headers)
    assert response.status_code == 409


def test_add_to_watchlist_max_limit(client, stocks_in_db, auth_user, db_session: Session):
    """Req 6.6 — Adding the 51st stock should return HTTP 400."""
    headers = {"Authorization": f"Bearer {auth_user}"}

    # Get the user from DB
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()

    # Create 50 extra stocks and fill the watchlist directly via DB
    extra_stocks = []
    for i in range(50):
        s = Stock(code=f"XX{i:02d}", name=f"Extra Stock {i}", sector="Test", is_active=True)
        db_session.add(s)
        extra_stocks.append(s)
    db_session.flush()

    for s in extra_stocks:
        db_session.add(Watchlist(user_id=user.id, stock_id=s.id))
    db_session.commit()

    # Now try to add one more (BBCA) — should hit the 50-item limit
    response = client.post("/api/v1/watchlist/", json={"code": "BBCA"}, headers=headers)
    assert response.status_code == 400


def test_remove_from_watchlist(client, stocks_in_db, auth_user):
    """Req 6.5 — DELETE /watchlist/{code} should successfully remove a stock."""
    headers = {"Authorization": f"Bearer {auth_user}"}
    # Add first
    client.post("/api/v1/watchlist/", json={"code": "TLKM"}, headers=headers)
    # Then remove
    response = client.delete("/api/v1/watchlist/TLKM", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "TLKM" in data["message"]


# ---------------------------------------------------------------------------
# Ranking tests
# ---------------------------------------------------------------------------


def test_ranking_pagination(client, stocks_with_scores):
    """Req 7.5 — GET /ranking?page=1&per_page=5 should return 5 items and correct total."""
    response = client.get("/api/v1/ranking/?page=1&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5
    assert data["total"] == 7  # 7 stocks inserted
    assert data["page"] == 1
    assert data["per_page"] == 5


def test_ranking_sort_by_score(client, stocks_with_scores):
    """Req 7.3 — GET /ranking?sort_by=score&sort_order=desc should return highest score first."""
    response = client.get("/api/v1/ranking/?sort_by=score&sort_order=desc&per_page=10")
    assert response.status_code == 200
    data = response.json()
    items = data["data"]
    scores = [item["score"] for item in items if item["score"] is not None]
    assert scores == sorted(scores, reverse=True), "Scores should be in descending order"


def test_ranking_filter_by_sector(client, stocks_with_scores):
    """Req 7.4 — GET /ranking?sector=Keuangan should only return stocks in Keuangan sector."""
    response = client.get("/api/v1/ranking/?sector=Keuangan&per_page=10")
    assert response.status_code == 200
    data = response.json()
    items = data["data"]
    assert len(items) > 0
    for item in items:
        assert item["sector"] == "Keuangan", f"Expected sector Keuangan, got {item['sector']}"
