from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from typing import Optional
from jose import jwt, JWTError
from sqlalchemy import select
import json

from core.config import settings
from db.database import async_session_maker
from memory.models import User
from voice.buffer import AudioBuffer
from voice.session import VoiceSession
from voice.transcriber import transcribe_chunk

router = APIRouter()

async def get_current_user_ws(token: str = Query(...)) -> Optional[User]:
    """Verify JWT token and return user."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
        
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user

class VoiceConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = VoiceConnectionManager()

@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    user: Optional[User] = Depends(get_current_user_ws)
):
    # Authentication
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    
    # Initialize session state
    session = VoiceSession(user.id)
    buffer = AudioBuffer()
    
    try:
        while True:
            # Expect binary message by default for audio
            # But might get text for control messages
            # We can use receive() which returns a dict
            
            message = await websocket.receive()
            
            if "bytes" in message and message["bytes"]:
                # Binary audio chunk
                data = message["bytes"]
                session.add_metric_audio(len(data))
                buffer.add(data)
                session.touch()
                
                # Check buffer
                # For now, simplistic check: 
                # If buffer > 32KB (approx 1s) OR every N chunks
                # A better approach for "Real-time" is to send immediately or small buffer.
                # But Groq API is HTTP request, latency overhead.
                # Let's try buffering ~1-2 seconds.
                
                if buffer.is_ready():
                    audio_chunk = buffer.flush()
                    
                    # Notify processing
                    await websocket.send_json({
                        "type": "status", 
                        "state": "processing"
                    })
                    
                    # Transcribe
                    text = await transcribe_chunk(audio_chunk)
                    
                    if text:
                        await websocket.send_json({
                            "type": "transcript",
                            "text": text,
                            "is_final": False # Streaming partials logic is complex, simple chunking here
                        })
            
            elif "text" in message and message["text"]:
                # Control message
                try:
                    data = json.loads(message["text"])
                    if data.get("action") == "stop":
                        # Flush remaining
                        pass 
                except:
                    pass
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        session.close()
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket)
