import pytest
import numpy as np
from fastapi.testclient import TestClient
from main import app
from ai.features import extract_features
from ai.model import AnomalyDetector
from services.simulator import generate_normal_event, generate_attack_event

client = TestClient(app)


# Level 1 - Feature extraction
def test_extract_features_returns_array():
    event = generate_normal_event()
    features = extract_features(event)
    assert isinstance(features, np.ndarray)
    assert len(features) == 15
    assert not np.any(np.isnan(features))

def test_extract_features_attack_event():
    event = generate_attack_event()
    features = extract_features(event)
    assert isinstance(features, np.ndarray)
    assert len(features) == 15

def test_extract_features_handles_missing_flags():
    event = generate_normal_event()
    event["flags"] = {}
    features = extract_features(event)
    assert features[12] == 0.0
    assert features[13] == 0.0
    assert features[14] == 0.0


# Level 2 - Model training and prediction
def test_model_trains_successfully():
    detector = AnomalyDetector()
    events = [generate_normal_event() for _ in range(160)]
    events += [generate_attack_event() for _ in range(40)]
    detector.train(events)
    assert detector.is_trained == True

def test_model_requires_minimum_events():
    detector = AnomalyDetector()
    with pytest.raises(ValueError):
        detector.train([generate_normal_event() for _ in range(5)])

def test_model_predict_returns_correct_shape():
    detector = AnomalyDetector()
    events = [generate_normal_event() for _ in range(160)]
    events += [generate_attack_event() for _ in range(40)]
    detector.train(events)

    result = detector.predict(generate_normal_event())
    assert "is_anomaly" in result
    assert "confidence_score" in result
    assert "severity" in result
    assert 0.0 <= result["confidence_score"] <= 1.0

def test_untrained_model_returns_safe_default():
    detector = AnomalyDetector()
    result = detector.predict(generate_normal_event())
    assert result["is_anomaly"] == False
    assert result["confidence_score"] == 0.0
    assert result["severity"] is None


# Level 3 - API endpoints
def test_model_status_endpoint():
    response = client.get("/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_trained" in data
    assert "model_type" in data

def test_train_endpoint():
    response = client.post("/ai/train")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["sample_size"] == 200