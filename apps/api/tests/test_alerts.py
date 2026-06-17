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

# Level 1 - Happy path
def test_get_alerts_returns_list():
    response = client.get("/alerts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_unread_count():
    response = client.get("/alerts/count")
    assert response.status_code == 200
    data = response.json()
    assert "unread_count" in data
    assert data["unread_count"] >= 0

def test_mark_all_read():
    response = client.patch("/alerts/mark-all-read")
    assert response.status_code == 200
    assert response.json()["message"] == "All alerts marked as read"

# Level 2 - Edge cases
def test_get_read_alerts():
    response = client.get("/alerts/?is_read=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_alerts_with_limit():
    response = client.get("/alerts/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) <= 5

# Level 3 - Failure cases
def test_mark_alert_read_not_found():
    fake_id = str(uuid.uuid4())
    response = client.patch(f"/alerts/{fake_id}/read", json={"is_read": True})
    assert response.status_code == 404

def test_mark_alert_read_invalid_uuid():
    response = client.patch("/alerts/not-a-uuid/read", json={"is_read": True})
    assert response.status_code == 422

def test_mark_alert_read_missing_body():
    fake_id = str(uuid.uuid4())
    response = client.patch(f"/alerts/{fake_id}/read")
    assert response.status_code == 422