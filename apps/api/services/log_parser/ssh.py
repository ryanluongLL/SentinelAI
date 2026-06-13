import re
from datetime import datetime, timezone
from typing import Optional

FAILED_PASSWORD_PATTERN = re.compile(
    r'Failed password for (?:invalid user )?(?P<username>\S+) '
    r'from (?P<source_ip>\S+) port (?P<port>\d+)'
)

ACCEPTED_PASSWORD_PATTERN = re.compile(
    r'Accepted (?:password|publickey) for (?P<username>\S+) '
    r'from (?P<source_ip>\S+) port (?P<port>\d+)'
)

INVALID_USER_PATTERN = re.compile(
    r'Invalid user (?P<username>\S+) '
    r'from (?P<source_ip>\S+) port (?P<port>\d+)'
)

DISCONNECTED_PATTERN = re.compile(
    r'Disconnected from (?:invalid user )?(?P<username>\S+)? '
    r'(?P<source_ip>\S+) port (?P<port>\d+)'
)

CONNECTION_CLOSED_PATTERN = re.compile(
    r'Connection closed by (?:invalid user )?(?P<username>\S+)? '
    r'(?P<source_ip>\S+) port (?P<port>\d+)'
)

SUSPICIOUS_USERNAMES = [
    "root", "admin", "administrator", "ubuntu", "ec2-user",
    "pi", "oracle", "postgres", "mysql", "test", "guest",
    "deploy", "ansible", "jenkins", "git", "www-data"
]

def classify_ssh_event(line: str) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None
    
    event_type = None
    match = None
    is_anomaly = False
    threat_type = None

    failed_match = FAILED_PASSWORD_PATTERN.search(line)

    if failed_match:
        match = failed_match
        event_type="failed_password"
        is_anomaly = True
        threat_type = "brute_force"

    if not match:
        accepted_match = ACCEPTED_PASSWORD_PATTERN.search(line)
        if accepted_match:
            match = accepted_match
            event_type = "accepted_login"
            is_anomaly = False
    
    if not match:
        invalid_match = INVALID_USER_PATTERN.search(line)
        if invalid_match:
            match = invalid_match
            event_type = "invalid_user"
            is_anomaly = True
            threat_type = "brute_force"

    if not match:
        disconnected_match = DISCONNECTED_PATTERN.search(line)
        if disconnected_match:
            match = disconnected_match
            event_type = "disconnected"
            is_anomaly = False
    
    if not match:
        closed_match = CONNECTION_CLOSED_PATTERN.search(line)
        if closed_match:
            match = closed_match
            event_type = "connection_closed"
            is_anomaly = False

    if not match:
        return None

    data = match.groupdict()
    source_ip = data.get("source_ip", "0.0.0.0")
    port = int(data.get("port", 22))
    username = data.get("username") or "unknown"

    is_suspicious_username = username.lower() in SUSPICIOUS_USERNAMES
    if is_suspicious_username and event_type == "failed_password":
        threat_type = "brute_force"
        is_anomaly = True
    
    bytes_transferred = 0
    if event_type == "accepted_login":
        bytes_transferred = 1024
    elif event_type in ["failed_password", "invalid_user"]:
        bytes_transferred = 256

    return{
        "source_ip": source_ip,
        "destination_ip": "0.0.0.0",
        "source_port": port,
        "destination_port": 22,
        "protocol": "SSH",
        "bytes_transferred": bytes_transferred,
        "packet_count": 1,
        "duration_ms": 0.0,
        "flags":{
            "syn": event_type in ["failed_password", "invalid_user"],
            "ack": event_type == "accepted_login",
            "fin": event_type in ["disconnected", "connection_closed"]
        },
        "raw_payload": line,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_anomaly": is_anomaly,
        "threat_type": threat_type,
        "metadata":{
            "event_type": event_type,
            "username": username,
            "port": port,
            "is_suspicious_username": is_suspicious_username,
            "is_failed_attempt": event_type in ["failed_password", "invalid_user" ]
        }
    }

def parse_ssh_file(filepath: str) -> list[dict]:
    events = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                parsed = classify_ssh_event(line)
                if parsed:
                    events.append(parsed)
    except FileNotFoundError:
        raise FileNotFoundError(f"SSH log file not found: {filepath}")
    return events

def parse_ssh_lines(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        parsed = classify_ssh_event(line)
        if parsed:
            events.append(parsed)
    return events