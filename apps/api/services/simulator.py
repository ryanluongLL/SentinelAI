import random
import asyncio
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

NORMAL_PORTS = [80, 443, 22, 53, 8080, 3000, 5432, 6379]
SUSPICIOUS_PORTS = [4444, 6666, 1337, 31337, 9999]
PROTOCOLS = ["TCP", "UDP", "HTTP", "HTTPS", "DNS", "SSH"]

ATTACK_PATTERNS = {
    "ddos":{
        "description": "High volume traffic from single source",
        "bytes_range": (50000, 500000),
        "packet_range": (1000, 10000),
        "duration_range": (0.1, 1.0),
    },

    "port_scan":{
        "description": "Sequential port scanning detected",
        "bytes_range": (40,120),
        "packet_range": (1,3),
        "duration_range": (0.01, 0.05),
    },

    "malware":{
        "description": "Suspicious outbound connection to known bad IP",
        "bytes_range": (500, 5000),
        "packet_range": (10,50),
        "duration_range": (5.0, 30.0),
    },
    
    "brute_force":{
        "description": "Repeated failed authentication attempts",
        "bytes_range": (200, 800),
        "packet_range": (5,20),
        "duration_range": (0.5, 2.0),
    },
}

def generate_normal_event() -> dict:
    return{
        "source_ip": fake.ipv4(),
        "destination_ip": fake.ipv4_private(),
        "source_port": random.randint(1024, 65535),
        "destination_port": random.choice(NORMAL_PORTS),
        "protocol": random.choice(PROTOCOLS),
        "bytes_transferred": random.randint(100, 10000),
        "packet_count": random.randint(1,100),
        "duration_ms": round(random.uniform(1.0, 500.0), 2),
        "flags": {"syn": False, "ack": True, "fin": False},
        "raw_payload": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_anomaly": False,
        "threat_type": None,
    }

def generate_attack_event() -> dict:
    attack_type = random.choice(list(ATTACK_PATTERNS.keys()))
    pattern = ATTACK_PATTERNS[attack_type]

    return{
        "source_ip": fake.ipv4(),
        "destination_ip": fake.ipv4_private(),
        "source_port": random.randint(1024, 65535),
        "destination_port": random.choice(SUSPICIOUS_PORTS),
        "protocol": random.choice(PROTOCOLS),
        "bytes_transferred": random.randint(*pattern["bytes_range"]),
        "packet_count": random.randint(*pattern["packet_range"]),
        "duration_ms": round(random.uniform(*pattern["duration_range"]) * 1000, 2),
        "flags": {"syn": True, "ack": False, "fin": False},
        "raw_payload": f"ATTACK_PATTERN_{attack_type.upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_anomaly": True,
        "threat_type": attack_type,
    }

async def generate_event_stream(attack_probability: float = 0.2):
    """
    Continuously yields network events.
    20% change of being an attack event by default.
    """
    while True:
        if random.random() < attack_probability:
            event = generate_attack_event()
        else:
            event = generate_normal_event()
        
        yield event
        await asyncio.sleep(random.uniform(0.5, 2.0))