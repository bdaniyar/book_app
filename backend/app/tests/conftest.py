import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load backend/.env for test runs (so TEST_DATABASE_URL/DATABASE_URL/JWT_SECRET_KEY are available)
load_dotenv(override=False)

from app.main import create_app
from app.db.base import Base
from app.api.deps import db as db_dep


@pytest.fixture(scope="session")
def test_engine():
    # Never fall back to DATABASE_URL: the test suite executes writes and must
    # only ever connect to an explicitly named, dedicated test database.
    raw_test_url = os.getenv("TEST_DATABASE_URL")
    if not raw_test_url:
        raise RuntimeError("TEST_DATABASE_URL must be explicitly set for tests")

    test_url = make_url(raw_test_url)
    database_name = (test_url.database or "").lower()
    if not re.search(r"(^|[_-])test($|[_-])", database_name):
        raise RuntimeError(
            "Refusing to run tests: TEST_DATABASE_URL database name must contain "
            "a separate 'test' segment"
        )

    raw_application_url = os.getenv("DATABASE_URL")
    if raw_application_url and test_url == make_url(raw_application_url):
        raise RuntimeError(
            "Refusing to run tests: TEST_DATABASE_URL matches DATABASE_URL"
        )

    engine = create_engine(test_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    connection = test_engine.connect()
    outer_transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def reset_in_memory_rate_limits():
    from app.api.v1.endpoints.auth import _RATE_LIMITS

    _RATE_LIMITS.clear()
    yield
    _RATE_LIMITS.clear()


@pytest.fixture()
def client(db_session: Session):
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[db_dep.get_db] = _override_get_db

    with TestClient(app) as c:
        yield c
