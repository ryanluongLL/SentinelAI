from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from websocket.stream import stream_events

app = FastAPI(title="SentinelAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SentinelAI API"}

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await stream_events(websocket)