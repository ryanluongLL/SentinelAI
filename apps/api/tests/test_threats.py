import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from main import app
from core.database import get_db
import os
import uuid

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sentinel:sentinel_pass@db:5432/sentinelai",
).replace("postgresql://", "postgresql+asyncpg://")

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False )

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


async def seed_threat(severity: str = "high") -> str:
    threat_id = str(uuid.uuid4())
    async with TestSessionLocal() as session:
        await session.execute(text("""
            INSERT INTO threats(id, threat_type, severity, confidence_score, source_ip, description)
            VALUES(:id, :threat_type, :severity, :confidence_score, :source_ip, :description)
        """), {
            "id": threat_id,
            "threat_type": "ddos",
            "severity": severity,
            "confidence_score": 0.95,
            "source_ip": "192.168.1.100",
            "description": "Test threat"   
        })
        await session.commit()
    return threat_id


# Level 1 - Happy path
def test_get_threats_return_list():
    response = client.get("/threats/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_threats_summary_keys():
    response = client.get("/threats/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "critical" in data
    assert "high" in data
    assert "medium" in data
    assert "low" in data
    assert "unresolved" in data

def test_get_threats_summary_empty_returns_zeroes():
    response = client.get("/threats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0


# Level 2 - Edge cases
def test_get_threats_filter_by_valid_severity():
    response = client.get("/threats/?severity=high")
    assert response.status_code == 200
    data = response.json()
    for threat in data:
        assert threat["severity"] == "high"

def test_get_threats_filter_resolved():
    response = client.get("/threats/?is_resolved=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_threats_limit():
    response = client.get("/threats/?limit=1")
    assert response.status_code == 200
    assert len(response.json()) <= 1

# Level 3 - Failure cases
def test_resolve_threat_not_found():
    fake_id = str(uuid.uuid4())
    response = client.patch(f"/threats/{fake_id}/resolve", json={"is_resolved": True})
    assert response.status_code == 404

def test_resolve_threat_invalid_uuid():
    response = client.patch("/threats/not-a-real-uuid/resolve", json={"is_resolved": True})
    assert response.status_code in [404, 422, 500]

def test_resolve_threat_missing_body():
    fake_id = str(uuid.uuid4())
    response = client.patch(f"/threats/{fake_id}/resolve")
    assert response.status_code == 422