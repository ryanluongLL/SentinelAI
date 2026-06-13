# nginx / Apache access logs
#  Every web server produces these. Format is well documented (combined log format), each line has IP, timestamp, method, path, status code, bytes, user agent. The anomaly story is strong: you can detect scanners hammering 404s, sudden request spikes from one IP, unusual user agents, path traversal attempts (../../etc/passwd)
import re
from datetime import datetime, timezone
from typing import Optional

NGINX_LOG_PATTERN = re.compile(
    r'(?P<source_ip>\S+)\s+'
    r'\S+\s+'
    r'\S+\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<bytes>\d+|-)\s+'
    r'"(?P<referer>[^"]*)"\s+'
    r'"(?P<user_agent>[^"]*)"'
)

SUSPICIOUS_PATHS = [
    "etc/passwd", "etc/shadow", "../", "..%2f",
    ".env", "wp-admin", "phpinfo", ".git",
    "admin", "shell", "cmd", "exec"
]

SUSPICIOUS_METHODS = ["TRACE", "TRACK", "OPTIONS", "CONNECT"]

HTTP_METHOD_MAP = {
    "GET": 0, "POST": 1, "PUT": 2, "DELETE": 3,
    "PATCH": 4, "HEAD": 5, "OPTIONS": 6, "TRACE": 7,
    "CONNECT": 8, "OTHER": 9
}

def parse_nginx_line(line: str) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None

    match = NGINX_LOG_PATTERN.match(line)
    if not match:
        return None

    data = match.groupdict()

    try:
        bytes_transferred = int(data["bytes"]) if data["bytes"] != "-" else 0
        status_code = int(data["status"])
        method = data["method"].upper()
        path = data["path"].lower()
        user_agent = data["user_agent"].lower()

        is_suspicious_path = any(p in path for p in SUSPICIOUS_PATHS)
        is_suspicious_method = method in SUSPICIOUS_METHODS
        is_scanner = any(s in user_agent for s in [
            "nmap", "nikto", "sqlmap", "masscan",
            "zgrab", "nuclei", "dirbuster", "gobuster"
        ])
        is_error = status_code >= 400
        is_server_error = status_code >= 500

        threat_type = None
        if is_scanner:
            threat_type = "port_scan"
        elif is_suspicious_path:
            threat_type = "malware"
        elif is_suspicious_method:
            threat_type = "anomaly"

        return {
            "source_ip": data["source_ip"],
            "destination_ip": "0.0.0.0",
            "source_port": 0,
            "destination_port": 443 if "https" in data["protocol"].lower() else 80,
            "protocol": "HTTPS" if status_code in [301, 302] else "HTTP",
            "bytes_transferred": bytes_transferred,
            "packet_count": 1,
            "duration_ms": 0.0,
            "flags": {
                "syn": is_suspicious_method,
                "ack": not is_error,
                "fin": is_error
            },
            "raw_payload": f"{method} {data['path']} {data['protocol']} {status_code}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_anomaly": is_suspicious_path or is_suspicious_method or is_scanner,
            "threat_type": threat_type,
            "metadata": {
                "method": method,
                "path": data["path"],
                "status_code": status_code,
                "user_agent": data["user_agent"],
                "bytes_transferred": bytes_transferred,
                "is_error": is_error,
                "is_server_error": is_server_error,
                "is_scanner": is_scanner,
                "is_suspicious_path": is_suspicious_path
            }
        }
    except Exception:
        return None

def parse_nginx_file(filepath: str) -> list[dict]:
    events = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                parsed = parse_nginx_line(line)
                if parsed:
                    events.append(parsed)
    except FileNotFoundError:
        raise FileNotFoundError(f"Nginx log file not found: {filepath}")
    return events

def parse_nginx_lines(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        parsed = parse_nginx_line(line)
        if parsed:
            events.append(parsed)
    return events