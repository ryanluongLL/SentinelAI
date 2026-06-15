from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.database import get_db
from services.log_parser.nginx import parse_nginx_lines
from services.log_parser.ssh import parse_ssh_lines
from ai.model import detector
from ai.detector import process_event
import uuid
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/logs", tags=["logs"])