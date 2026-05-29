import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ai.model import detector

THREAT_DESCRIPTIONS = {
    "ddos": "High volume traffic detected from a single source indicating a potential DDoS attack",
    "port_scan": "Sequential port scanning behavior detected indicating reconnaissance activity",
    "malware": "Suspicious outbound connection to a known malicious endpoint detected",
    "brute_force": "Repeated authentication attempts detected indicating a brute force attack",
    "anomaly": "Unusual network behavior detected that deviates significantly from baseline"
}

async def process_event(event: dict, db: AsyncSession) -> dict:
    result = detector.predict(event)

    if not result["is_anomaly"]:
        return{
            "event": event,
            "detection": result,
            "threat_id": None
        }
    
    threat_type = event.get("threat_type") or "anomaly"
    description = THREAT_DESCRIPTIONS.get(threat_type, THREAT_DESCRIPTIONS["anomaly"])
    threat_id = str(uuid.uuid4())

    threat_query = text("""
        INSERT INTO threats (
            id, detected_at, threat_type, severity,
            confidence_score, source_ip, description,
            is_resolved, metadata
        ) VALUES (
            CAST(:id AS UUID),
            :detected_at,
            :threat_type,
            :severity,
            :confidence_score,
            :source_ip,
            :description,
            false,
            CAST(:metadata AS JSONB)
        )
        RETURNING id::text
    """)

    await db.execute(threat_query, {
        "id": threat_id,
        "detected_at": datetime.now(timezone.utc),
        "threat_type": threat_type,
        "severity": result["severity"],
        "confidence_score": result["confidence_score"],
        "source_ip": event.get("source_ip", "unknown"),
        "description": description,
        "metadata": json.dumps({
            "destination_ip": event.get("destination_ip"),
            "destination_port": event.get("destination_port"),
            "protocol": event.get("protocol"),
            "bytes_transferred": event.get("bytes_transferred"),
            "packet_count": event.get("packet_count")
        })
    })

    alert_query = text("""
        INSERT INTO alerts (id, threat_id, created_at, is_read, message)
        VALUES (
            CAST(:id AS UUID),
            CAST(:threat_id AS UUID),
            :created_at,
            false,
            :message                   
    )
""")
    
    await db.execute(alert_query, {
        "id": str(uuid.uuid4()),
        "threat_id": threat_id,
        "created_at": datetime.now(timezone.utc),
        "message": f"{result}"
    })

    await db.commit()

    return{
        "event": event,
        "detection": result,
        "threat_id": threat_id
    }

async def train_model_from_simulator(sample_size: int = 200) -> dict:
    from services.simulator import generate_normal_event, generate_attack_event
    import random

    events = []
    for _ in range(int(sample_size * 0.8)):
        events.append(generate_normal_event())
    for _ in range(int(sample_size * 0.2)):
        events.append(generate_attack_event())

    random.shuffle(events)

    detector.train(events)
    return{
        "status": "ok",
        "message": f"Model trained on {len(events)} events",
        "sample_size": len(events)
    }