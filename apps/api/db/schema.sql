CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS network_events (
    id UUID DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_ip INET,
    destination_ip INET,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(20),
    bytes_transferred BIGINT,
    packet_count INTEGER,
    duration_ms FLOAT,
    flags JSONB DEFAULT '{}',
    raw_payload TEXT
);

SELECT create_hypertable('network_events', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS threats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    threat_type VARCHAR(100),
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    source_ip INET,
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    threat_id UUID REFERENCES threats(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats(severity);
CREATE INDEX IF NOT EXISTS idx_threats_detected_at ON threats(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);