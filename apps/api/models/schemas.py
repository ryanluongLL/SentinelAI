from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
import uuid

class NetworkEventCreate(BaseModel):
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    bytes_transferred: int
    packet_count: int
    duration_ms: float
    flags: dict = {}
    raw_payload: Optional[str] = None

class NetworkEventResponse(NetworkEventCreate):
    id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

class ThreatResponse(BaseModel):
    id: UUID
    event_id: Optional[UUID]
    detected_at: datetime
    threat_type: str
    severity: str
    confidence_score: float
    source_ip: str
    description: str
    is_resolved: bool
    metadata: dict = {}

    class Config:
        from_attributes = True

class ThreatResolveRequest(BaseModel):
    is_resolved: bool

class AlertResponse(BaseModel):
    id: UUID
    threat_id: UUID
    created_at: datetime
    is_read: bool
    message: str

    class Config:
        from_attributes = True

class AlertMarkReadRequest(BaseModel):
    is_read: bool

class DashboardStats(BaseModel):
    total_events: int
    total_threats: int
    critical_threats: int
    high_threats: int
    medium_threats: int
    low_threats: int
    unread_alerts: int
    events_last_hour: int