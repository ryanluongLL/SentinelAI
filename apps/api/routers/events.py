# ingesting raw network events into the database and retrieving them for the dashboard. The POST /events endpoint is what the AI model will call every time it processes a new packet. The GET /events endpoint is what your frontend calls to display the live feed.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.database import get_db
from models.schemas import NetworkEventCreate, NetworkEventResponse
from typing import List
from datetime import datetime, timezone
import uuid
import json


router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=dict)
async def ingest_event(event: NetworkEventCreate, db: AsyncSession = Depends(get_db)):
    query = text("""
        INSERT INTO network_events (
            id, timestamp, source_ip, destination_ip,
            source_port, destination_port, protocol,
            bytes_transferred, packet_count, duration_ms, flags, raw_payload
        ) VALUES (
            :id, :timestamp, :source_ip, :destination_ip, :source_port, :destination_port, :protocol, :bytes_transferred, :packet_count, :duration_ms, :flags, :raw_payload)
                 """)
    
    await db.execute(query,{
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc),
        "source_ip": event.source_ip,
        "destination_ip": event.destination_ip,
        "source_port": event.source_port,
        "destination_port": event.destination_port,
        "protocol": event.protocol,
        "bytes_transferred": event.bytes_transferred,
        "packet_count": event.packet_count,
        "duration_ms": event.duration_ms,
        "flags": json.dumps(event.flags),
        "raw_payload": event.raw_payload,
    })

    return {"status": "ok", "message": "Event ingested successfully"}

@router.get("/", response_model=List[dict])
async def get_events(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db)
):
    query = text("""
        SELECT
            id::text,
            timestamp,
            source_ip::text,
            destination_ip::text,
            source_port,
            destination_port,
            protocol,
            bytes_transferred,
            packet_count,
            duration_ms
        FROM network_events
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, {"limit": limit, "offset": offset})
    rows = result.fetchall()

    return [dict(row._mapping) for row in rows]

@router.get("/stats", response_model=dict)
async def get_event_stats(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT
                 COUNT(*) as total_events,
                 COUNT(CASE WHEN timestamp > NOW() - INTERVAL '1 hour' THEN 1 END) as events_last_hour,                    
                 COUNT(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN 1 END) as events_last_24h
        FROM network_events
""")
    
    result = await db.execute(query)
    row = result.fetchone()
    return dict(row._mapping)

