import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load backend/.env for test runs (so TEST_DATABASE_URL/DATABASE_URL/JWT_SECRET_KEY are available)
load_dotenv(override=False)

from app.main import create_app
from app.db.base import Base
from app.api.deps import db as db_dep


@pytest.fixture(scope="session")
def test_engine():
    # Use a dedicated DB url for tests if provided, otherwise fall back to DATABASE_URL.
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("TEST_DATABASE_URL (or DATABASE_URL) must be set for tests")
    engine = create_engine(db_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False
    )
    Base.metadata.create_all(bind=test_engine)

    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session):
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[db_dep.get_db] = _override_get_db

    with TestClient(app) as c:
        yield c
