import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from ai.features import extract_batch_features, extract_features

MODEL_PATH = "/app/ai/model.pkl"

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.2,
            random_state=42,
            max_samples="auto"
        )
        self.is_trained = False

    def train(self, events:list[dict]) -> None:
        if len(events) < 10:
            raise ValueError("Need at least 10 events to train the model")
        
        features = extract_batch_features(events)
        self.model.fit(features)
        self.is_trained = True
        self.save()
        print(f"Model trained on {len(events)} events and saved to disk")
    
    def predict(self, event: dict) -> dict:
        if not self.is_trained:
            return{
                "is_anomaly": False,
                "confidence_score": 0.0,
                "severity": None
            }
        features = extract_features(event).reshape(1, -1)
        prediction = self.model.predict(features)[0]
        anomaly_score = self.model.score_samples(features)[0]

        normalized_score = 1 - (anomaly_score + 0.5)
        confidence = float(np.clip(normalized_score, 0.0, 1.0))

        is_anomaly = prediction == -1

        severity = None
        if is_anomaly:
            if confidence >= 0.85:
                severity = "critical"
            elif confidence >= 0.70:
                severity - "high"
            elif confidence >= 0.55:
                severity - "medium"
            else:
                severity = "low"
            
        return {
            "is_anomaly": is_anomaly,
            "confidence_score": round(confidence, 4),
            "severity": severity
        }

    def save(self) -> None:
        joblib.dump(self.model, MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")
    
    def load(self) -> bool:
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.is_trained = True
            print("Model loaded from disk")
            return True
        return False
    
detector = AnomalyDetector()
detector.load()