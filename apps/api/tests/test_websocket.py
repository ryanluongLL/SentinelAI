import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "SentinelAI API"

def test_websocket_receives_event():
    with client.websocket_connect("/ws/events") as websocket:
        data = websocket.receive_json()
        assert "type" in data
        assert "data" in data
        assert data["type"] == "network_event"
        payload = data["data"]
        assert "source_ip" in payload
        assert "destination_ip" in payload
        assert "is_anomaly" in payload
        assert isinstance(payload["is_anomaly"], bool)