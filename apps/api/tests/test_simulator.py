import pytest
from services.simulator import generate_normal_event, generate_attack_event

def test_normal_event_shape():
    event = generate_normal_event()
    assert "source_ip" in event
    assert "destination_ip" in event
    assert event["is_anomaly"] == False
    assert event["threat_type"] is None

def test_attack_event_shape():
    event = generate_attack_event()
    assert event["is_anomaly"] == True
    assert event["threat_type"] is not None
    assert event["threat_type"] in ["ddos", "port_scan", "malware", "brute_force"]

def test_attack_event_uses_suspicious_port():
    SUSPICIOUS_PORTS = [4444, 6666, 1337, 31337, 9999]
    event = generate_attack_event()
    assert event["destination_port"] in SUSPICIOUS_PORTS