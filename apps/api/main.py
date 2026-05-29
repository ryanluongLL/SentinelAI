from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from websocket.stream import stream_events
from routers import events, threats, alerts
from ai.detector import train_model_from_simulator
from ai.model import detector


app = FastAPI(title="SentinelAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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