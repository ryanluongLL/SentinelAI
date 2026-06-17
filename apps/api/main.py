from fastapi import FastAPI, WebSocket, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from websocket.stream import stream_events
from routers import events, threats, alerts
from ai.detector import train_model_from_simulator
from ai.model import detector
from services.nlp_query import run_natural_language_query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



app = FastAPI(title="SentinelAI API", version="1.0.0")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NLQueryRequest(BaseModel):
    question: str

app.include_router(events.router)
app.include_router(threats.router)
app.include_router(alerts.router)



@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SentinelAI API"}

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await stream_events(websocket)

@app.post("/ai/train")
async def train_model():
    result = await train_model_from_simulator(sample_size=200)
    return result

@app.get("/ai/status")
async def model_status():
    return{
        "is_trained": detector.is_trained,
        "model_type": "IsolationForest",
        "contamination": 0.2,
        "n_estimators": 100
    }

@app.post("/query/natural")
@limiter.limit("10/minute")
async def natural_language_query(
    request: Request,
    body: NLQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    return await run_natural_language_query(body.question, db)