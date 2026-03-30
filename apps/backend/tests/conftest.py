"""
Pytest configuration and fixtures for auth service tests.

Uses SQLite in-memory database to avoid requiring an external PostgreSQL instance.
PostgreSQL-specific types (UUID, INET, JSONB) are patched to use SQLite-compatible
equivalents before models are imported.
"""

import json
import uuid
from typing import Generator

import pytest
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Patch PostgreSQL-specific types BEFORE importing any models
# ---------------------------------------------------------------------------

from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# --- UUID ---

_orig_uuid_dialect_impl = PG_UUID.dialect_impl
_orig_uuid_bind_proc = PG_UUID.bind_processor
_orig_uuid_result_proc = PG_UUID.result_processor


def _uuid_dialect_impl(self, dialect):
    if dialect.name == "sqlite":
        return dialect.type_descriptor(String(36))
    return _orig_uuid_dialect_impl(self, dialect)


def _uuid_bind_proc(self, dialect):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            return str(value)
        return process
    return _orig_uuid_bind_proc(self, dialect)


def _uuid_result_proc(self, dialect, coltype):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return uuid.UUID(value)
                except ValueError:
                    return value
            return value
        return process
    return _orig_uuid_result_proc(self, dialect, coltype)


PG_UUID.dialect_impl = _uuid_dialect_impl
PG_UUID.bind_processor = _uuid_bind_proc
PG_UUID.result_processor = _uuid_result_proc

# --- INET ---

_orig_inet_dialect_impl = INET.dialect_impl


def _inet_dialect_impl(self, dialect):
    if dialect.name == "sqlite":
        return dialect.type_descriptor(String(45))
    return _orig_inet_dialect_impl(self, dialect)


INET.dialect_impl = _inet_dialect_impl

# Patch SQLite type compiler to handle INET directly (needed for DDL)
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler  # noqa: E402

if not hasattr(SQLiteTypeCompiler, "visit_INET"):
    def _visit_inet(self, type_, **kw):
        return "VARCHAR(45)"
    SQLiteTypeCompiler.visit_INET = _visit_inet

# --- JSONB ---

_orig_jsonb_dialect_impl = JSONB.dialect_impl
_orig_jsonb_bind_proc = JSONB.bind_processor
_orig_jsonb_result_proc = JSONB.result_processor


def _jsonb_dialect_impl(self, dialect):
    if dialect.name == "sqlite":
        return dialect.type_descriptor(Text())
    return _orig_jsonb_dialect_impl(self, dialect)


def _jsonb_bind_proc(self, dialect):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            return json.dumps(value)
        return process
    return _orig_jsonb_bind_proc(self, dialect)


def _jsonb_result_proc(self, dialect, coltype):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                return json.loads(value)
            return value
        return process
    return _orig_jsonb_result_proc(self, dialect, coltype)


JSONB.dialect_impl = _jsonb_dialect_impl
JSONB.bind_processor = _jsonb_bind_proc
JSONB.result_processor = _jsonb_result_proc

# Patch SQLite type compiler to handle JSONB directly (needed for DDL)
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler  # noqa: E402

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    def _visit_jsonb(self, type_, **kw):
        return "TEXT"
    SQLiteTypeCompiler.visit_JSONB = _visit_jsonb

# ---------------------------------------------------------------------------
# Import models AFTER patching
# ---------------------------------------------------------------------------

from app.models.base import Base  # noqa: E402
from app.models import (  # noqa: E402, F401
    AIAnalysis,
    CorporateAction,
    DataSourceHealth,
    FundamentalData,
    LoginAttempt,
    PriceHistory,
    RefreshToken,
    SectorMetrics,
    Stock,
    StockPrice,
    StockScore,
    User,
    Watchlist,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create a SQLite in-memory engine shared across the test session."""
    _engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)
    _engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    """
    Provide a database session for each test.
    Deletes all rows from user-related tables after each test for isolation.
    """
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False)
    _SessionLocal.configure(bind=engine)
    session = _SessionLocal()

    yield session

    session.close()
    # Clean up data between tests (order matters due to FK constraints)
    with engine.begin() as conn:
        conn.execute(RefreshToken.__table__.delete())
        conn.execute(LoginAttempt.__table__.delete())
        conn.execute(User.__table__.delete())
