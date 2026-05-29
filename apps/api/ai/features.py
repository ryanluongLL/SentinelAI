import numpy as np

PROTOCOL_MAP = {
    "TCP": 0,
    "UDP": 1,
    "HTTP": 2,
    "HTTPS": 3,
    "DNS": 4,
    "SSH": 5,
    "ICMP": 6,
    "OTHER": 7,
}

SUSPICIOUS_PORTS = {4444, 6666, 1337, 31337, 9999, 1234, 8888}
COMMON_PORTS = {80, 443, 22, 53, 8080, 3000, 5432, 6379, 3306}

def extract_features(event: dict)-> np.ndarray:
    protocol_encoded = PROTOCOL_MAP.get(
        str(event.get("protocol", "OTHER")).upper(), 7
    )

    dst_port = int(event.get("destination_port", 0))
    src_port = int(event.get("source_port", 0))
    bytes_transferred = float(event.get("bytes_transferred", 0))
    packet_count = float(event.get("packet_count", 0))
    duration_ms = float(event.get("duration_ms", 0))

    is_suspicious_port = 1.0 if dst_port in SUSPICIOUS_PORTS else 0.0
    is_common_port = 1.0 if dst_port in COMMON_PORTS else 0.0
    is_high_port = 1.0 if dst_port > 49151 else 0.0
    is_privileged_port = 1.0 if dst_port < 1024 else 0.0

    bytes_per_packet = bytes_transferred / max(packet_count, 1)
    bytes_per_ms = bytes_transferred / max(duration_ms, 0.001)

    flags = event.get("flags", {})
    if isinstance(flags, str):
        import json
        try:
            flags = json.loads(flags)
        except Exception:
            flags = {}
    
    syn_flag = 1.0 if flags.get("syn", False) else 0.0
    ack_flag = 1.0 if flags.get("ack", False) else 0.0
    fin_flag = 1.0 if flags.get("fin", False) else 0.0

    features = np.array([
        protocol_encoded,
        dst_port,
        src_port,
        bytes_transferred,
        packet_count,
        duration_ms,
        is_suspicious_port,
        is_common_port,
        is_high_port,
        is_privileged_port,
        bytes_per_packet,
        bytes_per_ms,
        syn_flag,
        ack_flag,
        fin_flag,
    ], dtype=np.float64)

    return features

def extract_batch_features(events: list[dict]) -> np.ndarray:
    return np.array([extract_features(e) for e in events])
