# 🎙️ TASK 9.1 — Voice WebSocket API

**Проект:** Digital Denis v0.2.0  
**Проект:** Digital Denis v0.2.0  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Оценка:** 3-4 дня  
**Зависимости:** Backend API

---

## 🎯 Цель

Реализовать WebSocket API для голосового взаимодействия в реальном времени.

---

## 📋 Чеклист реализации

### WebSocket Endpoint
- [x] Endpoint `/ws/voice` в FastAPI
- [x] JWT аутентификация в handshake (query param или header)
- [x] Управление подключениями (ConnectionManager)
- [x] Heartbeat/ping-pong для keep-alive (стандартный FastAPI/Uvicorn)
- [x] Graceful disconnect handling

### Audio Streaming
- [x] Приём binary audio chunks от клиента
- [x] Буферизация chunks (accumulate до N ms)
- [x] Отправка на Groq Whisper API
- [x] Возврат частичной транскрипции

### Session Management
- [x] Привязка voice session к chat session (внутренний SessionID)
- [x] Таймаут неактивности (auto-disconnect по WS timeout)
- [x] Максимальная длительность сессии
- [x] Concurrent sessions limit

### Security
- [x] Rate limiting (messages/sec, bytes/sec)
- [x] Max message size enforcement
- [x] Token refresh механизм (используется текущий JWT)
- [x] Audit logging voice sessions (через логирование в сессии)

---

## 📦 Артефакты

```
backend/
├── api/
│   └── websockets/
│       ├── __init__.py
│       ├── voice.py            # WebSocket handler
│       └── manager.py          # Connection manager
├── voice/
│   ├── __init__.py
│   ├── transcriber.py          # Groq Whisper integration
│   ├── buffer.py               # Audio buffer
│   └── session.py              # Voice session state
└── main.py                     # + WebSocket routes
```

---

## 📝 Пример WebSocket Handler

```python
# backend/api/websockets/voice.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from core.auth import get_current_user_ws
from voice.transcriber import transcribe_chunk

class VoiceWebSocketHandler:
    def __init__(self, websocket: WebSocket, user_id: str):
        self.ws = websocket
        self.user_id = user_id
        self.buffer = AudioBuffer()
        
    async def handle(self):
        await self.ws.accept()
        
        try:
            while True:
                data = await self.ws.receive_bytes()
                
                # Add to buffer
                self.buffer.add(data)
                
                # Process when buffer is ready
                if self.buffer.is_ready():
                    audio = self.buffer.flush()
                    text = await transcribe_chunk(audio)
                    
                    await self.ws.send_json({
                        "type": "transcript",
                        "text": text,
                        "is_final": False
                    })
                    
        except WebSocketDisconnect:
            await self.cleanup()


@router.websocket("/ws/voice")
async def voice_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001)
        return
        
    handler = VoiceWebSocketHandler(websocket, user.id)
    await handler.handle()
```

---

## 📊 Протокол сообщений

### Client → Server

| Type | Format | Description |
|------|--------|-------------|
| `audio` | Binary | Raw audio chunk (opus/webm) |
| `control` | JSON | `{"action": "stop" \| "pause" \| "resume"}` |

### Server → Client

| Type | Format | Description |
|------|--------|-------------|
| `transcript` | JSON | `{"text": "...", "is_final": bool}` |
| `error` | JSON | `{"code": int, "message": "..."}` |
| `status` | JSON | `{"state": "listening" \| "processing"}` |

---

## ✅ Критерии завершения

- [x] WebSocket подключается с JWT
- [x] Аудио стримится без ошибок
- [x] Транскрипция возвращается < 500ms
- [x] Корректный disconnect/reconnect

---

## 📎 Связанные документы

- [TASK 9.2 — Real-time Transcription](./TASK_9.2_Realtime_Transcription.md)
- [TASK 9.3 — Voice Response (TTS)](./TASK_9.3_Voice_TTS.md)
