# purpose of this test is to tests all three endpoints in your events router. It verifies that you can ingest an event into the database, retrieve it back, and get stats. This is an integration test, meaning it tests the full path from HTTP request all the way to the database.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from main import app
from core.database import get_db
import os

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sentinel:sentinel_pass@db:5432/sentinelai"
).replace("postgresql://", "postgresql+asyncpg://")

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

sample_event = {
    "source_ip": "192.168.1.100",
    "destination_ip": "10.0.0.1",
    "source_port": 54321,
    "destination_port": 80,
    "protocol": "TCP",
    "bytes_transferred": 1500,
    "packet_count": 10,
    "duration_ms": 25.5,
    "flags": {"syn": False, "ack": True, "fin": False},
    "raw_payload": None
}

def test_ingest_event():
    response = client.post("/events/", json=sample_event)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_events():
    response = client.get("/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_events_with_limit():
    response = client.get("/events/?limit=10")
    assert response.status_code == 200
    assert len(response.json()) <= 10

def test_get_event_stats():
    response = client.get("/events/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    assert "events_last_hour" in data
    assert "events_last_24h" in data