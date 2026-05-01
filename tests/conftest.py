import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import Base, get_db
from src.main import app

# Use a separate test database if TEST_DATABASE_URL is set, else use main DB
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", os.getenv("DATABASE_URL"))

test_engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import src.models  # noqa: F401
    Base.metadata.create_all(bind=test_engine)
    yield
    # Don't drop — leave data for inspection


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
