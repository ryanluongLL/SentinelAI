from services.log_parser.nginx import parse_nginx_line, parse_nginx_lines
from services.log_parser.ssh import classify_ssh_event, parse_ssh_lines

SAMPLE_NGINX_NORMAL = '192.168.1.1 - - [28/May/2026:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
SAMPLE_NGINX_SCANNER = '10.0.0.1 - - [28/May/2026:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "nikto/2.1.6"'
SAMPLE_NGINX_PATH_TRAVERSAL = '10.0.0.2 - - [28/May/2026:10:00:02 +0000] "GET /../../etc/passwd HTTP/1.1" 404 0 "-" "curl/7.68"'
SAMPLE_NGINX_ERROR = '10.0.0.3 - - [28/May/2026:10:00:03 +0000] "POST /login HTTP/1.1" 401 0 "-" "python-requests/2.28"'
SAMPLE_NGINX_MALFORMED = "this is not a valid nginx log line"

SAMPLE_SSH_FAILED = "May 28 10:00:00 server sshd[1234]: Failed password for root from 192.168.1.100 port 54321 ssh2"
SAMPLE_SSH_ACCEPTED = "May 28 10:00:01 server sshd[1234]: Accepted publickey for deploy from 10.0.0.1 port 22222 ssh2"
SAMPLE_SSH_INVALID = "May 28 10:00:02 server sshd[1234]: Invalid user admin from 45.33.32.156 port 12345"
SAMPLE_SSH_MALFORMED = "this is not a valid ssh log line"


# nginx happy path
def test_nginx_parses_normal_line():
    result = parse_nginx_line(SAMPLE_NGINX_NORMAL)
    assert result is not None
    assert result["source_ip"] == "192.168.1.1"
    assert result["is_anomaly"] == False
    assert result["threat_type"] is None

def test_nginx_detects_scanner():
    result = parse_nginx_line(SAMPLE_NGINX_SCANNER)
    assert result is not None
    assert result["is_anomaly"] == True
    assert result["threat_type"] == "port_scan"
    assert result["metadata"]["is_scanner"] == True

def test_nginx_detects_path_traversal():
    result = parse_nginx_line(SAMPLE_NGINX_PATH_TRAVERSAL)
    assert result is not None
    assert result["is_anomaly"] == True
    assert result["threat_type"] == "malware"
    assert result["metadata"]["is_suspicious_path"] == True

def test_nginx_parses_error_response():
    result = parse_nginx_line(SAMPLE_NGINX_ERROR)
    assert result is not None
    assert result["metadata"]["status_code"] == 401
    assert result["metadata"]["is_error"] == True

# nginx edge cases
def test_nginx_returns_none_for_malformed():
    result = parse_nginx_line(SAMPLE_NGINX_MALFORMED)
    assert result is None

def test_nginx_returns_none_for_empty():
    result = parse_nginx_line("")
    assert result is None

def test_nginx_parse_lines_skips_malformed():
    lines = [SAMPLE_NGINX_NORMAL, SAMPLE_NGINX_MALFORMED, SAMPLE_NGINX_SCANNER]
    results = parse_nginx_lines(lines)
    assert len(results) == 2


# ssh happy path
def test_ssh_detects_failed_password():
    result = classify_ssh_event(SAMPLE_SSH_FAILED)
    assert result is not None
    assert result["source_ip"] == "192.168.1.100"
    assert result["is_anomaly"] == True
    assert result["threat_type"] == "brute_force"
    assert result["metadata"]["event_type"] == "failed_password"
    assert result["metadata"]["username"] == "root"

def test_ssh_parses_accepted_login():
    result = classify_ssh_event(SAMPLE_SSH_ACCEPTED)
    assert result is not None
    assert result["is_anomaly"] == False
    assert result["metadata"]["event_type"] == "accepted_login"

def test_ssh_detects_invalid_user():
    result = classify_ssh_event(SAMPLE_SSH_INVALID)
    assert result is not None
    assert result["is_anomaly"] == True
    assert result["threat_type"] == "brute_force"
    assert result["metadata"]["event_type"] == "invalid_user"

# ssh edge cases
def test_ssh_returns_none_for_malformed():
    result = classify_ssh_event(SAMPLE_SSH_MALFORMED)
    assert result is None

def test_ssh_returns_none_for_empty():
    result = classify_ssh_event("")
    assert result is None

def test_ssh_parse_lines_skips_malformed():
    lines = [SAMPLE_SSH_FAILED, SAMPLE_SSH_MALFORMED, SAMPLE_SSH_INVALID]
    results = parse_ssh_lines(lines)
    assert len(results) == 2

def test_ssh_flags_suspicious_username():
    result = classify_ssh_event(SAMPLE_SSH_FAILED)
    assert result["metadata"]["is_suspicious_username"] == True