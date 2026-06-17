from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.database import get_db
from models.schemas import ThreatResolveRequest
from typing import List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/threats", tags=["threats"])

@router.get("/", response_model=List[dict])
async def get_threats(
    severity: str = Query(default=None),
    is_resolved: bool = Query(default=False),
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db)
):
    base_query = """
        SELECT
            id::text,
            detected_at,
            threat_type,
            severity,
            confidence_score,
            source_ip::text,
            description,
            is_resolved,
            metadata
        FROM threats
        WHERE is_resolved = :is_resolved
    """

    params = {"is_resolved": is_resolved, "limit": limit}

    if severity:
        base_query += " AND severity = :severity"
        params["severity"] = severity

    base_query += " ORDER BY detected_at DESC LIMIT :limit"

    result = await db.execute(text(base_query), params)
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]

@router.get("/summary")
async def get_threats_summary(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical,
            COUNT(CASE WHEN severity = 'high' THEN 1 END) as high,
            COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium,
            COUNT(CASE WHEN severity = 'low' THEN 1 END) as low,
            COUNT(CASE WHEN is_resolved = false THEN 1 END) as unresolved
        FROM threats
    """)
    result = await db.execute(query)
    row = result.fetchone()
    return dict(row._mapping)

@router.patch("/{threat_id}/resolve")
async def resolve_threat(
    threat_id: str,
    body: ThreatResolveRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid.UUID(threat_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    query = text("""
        UPDATE threats
        SET is_resolved = :is_resolved,
            resolved_at = :resolved_at
        WHERE id = CAST(:id AS UUID)
        RETURNING id::text, is_resolved
    """)

    result = await db.execute(query, {
        "id": threat_id,
        "is_resolved": body.is_resolved,
        "resolved_at": datetime.now(timezone.utc) if body.is_resolved else None
    })

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Threat not found")

    return {"id": row._mapping["id"], "is_resolved": row._mapping["is_resolved"]}