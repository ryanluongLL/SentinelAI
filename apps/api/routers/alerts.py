from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.database import get_db
from models.schemas import AlertMarkReadRequest
from typing import List
import uuid

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[dict])
async def get_alerts(
    is_read: bool = Query(default=False),
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db)
):
    query = text("""
        SELECT
            a.id::text,
            a.threat_id::text,
            a.created_at,
            a.is_read,
            a.message,
            t.severity,
            t.threat_type,
            t.source_ip::text
        FROM alerts a
        JOIN threats t ON a.threat_id = t.id
        WHERE a.is_read = :is_read
        ORDER BY a.created_at DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {"is_read": is_read, "limit": limit})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]

@router.get("/count")
async def get_unread_count(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT COUNT(*) as unread_count
        FROM alerts
        WHERE is_read = false
""")
    result = await db.execute(query)
    row = result.fetchone()
    return {"unread_count": row._mapping["unread_count"]}

@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    body: AlertMarkReadRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    
    query=text("""
        UPDATE alerts
        SET is_read = :is_read
        WHERE id = CAST(:id AS UUID)
        RETURNING id::text, is_read
""")
    
    result = await db.execute(query,{
        "id": alert_id,
        "is_read": body.is_read
    })

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"id": row._mapping["id"], "is_read": row._mapping["is_read"]}

@router.patch("/mark-all-read")
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    query = text("""
        UPDATE alerts
        SET is_read = true
        WHERE is_read = false
""")
    result = await db.execute(query)
    return {"message": "All alerts marked as read"}
    