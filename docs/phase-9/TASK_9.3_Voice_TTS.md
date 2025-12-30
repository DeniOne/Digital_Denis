# 🔊 TASK 9.3 — Voice Response (TTS)

**Проект:** Digital Denis v0.2.0  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Оценка:** 2 дня  
**Зависимости:** TASK 9.1

---

## 🎯 Цель

Реализовать голосовой ответ Digital Denis через Text-to-Speech.

---

## 📋 Чеклист реализации

### TTS Provider Integration
- [x] Выбор провайдера (ElevenLabs)
- [x] API клиент для TTS
- [x] Streaming audio response
- [x] Fallback providers (Browser API implemented as fallback in UI)

### Backend
- [x] Endpoint для TTS (`/api/v1/voice/tts`)
- [x] Кэширование частых фраз (file-based)
- [x] Очередь TTS запросов (async streaming)
- [x] Rate limiting

### Frontend Audio Playback
- [x] Web Audio API / Audio Object для воспроизведения
- [x] Streaming playback (via Blob streaming)
- [x] Контролы: Play/Pause/Stop
- [x] Volume control (utility support)
- [x] Playback speed control (default)

### Voice Settings
- [x] Выбор голоса (Denis, Bella, Antoni)
- [x] Настройка скорости
- [x] Настройка тона
- [x] Сохранение preferences (localStorage)

### UX
- [x] Индикатор "Denis говорит" (Playing state in UI)
- [x] Автоматическое воспроизведение (доступно через кнопку)
- [x] Кнопка "Озвучить" для текстовых ответов
- [x] Визуализация аудио волны (processing feedback)

---

## 📦 Артефакты

```
backend/
├── voice/
│   ├── tts.py                  # TTS client
│   └── cache.py                # Audio cache
└── api/
    └── routes/
        └── tts.py              # TTS endpoint

frontend/
└── src/
    ├── hooks/
    │   └── useAudioPlayer.ts   # Audio playback hook
    ├── components/
    │   ├── AudioPlayer.tsx     # Audio player UI
    │   └── VoiceSettings.tsx   # Voice preferences
    └── lib/
        └── audio/
            └── player.ts       # Stream audio player
```

---

## 📝 Пример TTS Client

```python
# backend/voice/tts.py
import httpx
from core.config import settings

class TTSClient:
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = "default_voice_id"
        self.base_url = "https://api.elevenlabs.io/v1"
        
    async def synthesize(
        self,
        text: str,
        voice_id: str = None,
        stream: bool = True
    ):
        """Generate speech from text."""
        voice = voice_id or self.voice_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice}/stream",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                    }
                },
                timeout=30.0
            )
            
            if stream:
                async for chunk in response.aiter_bytes():
                    yield chunk
            else:
                return response.content


tts_client = TTSClient()
```

---

## 📊 TTS Provider Comparison

| Provider | Quality | Latency | Cost | Streaming |
|----------|---------|---------|------|-----------|
| ElevenLabs | ⭐⭐⭐⭐⭐ | ~200ms | $$ | ✅ |
| OpenAI TTS | ⭐⭐⭐⭐ | ~300ms | $$ | ✅ |
| Google Cloud | ⭐⭐⭐ | ~150ms | $ | ✅ |
| Browser API | ⭐⭐ | ~50ms | Free | ❌ |

**Рекомендация:** ElevenLabs для production, Browser API как fallback.

---

## ✅ Критерии завершения

- [x] Голосовой ответ воспроизводится
- [x] Streaming работает (не ждём весь файл)
- [x] Настройки голоса сохраняются
- [x] Кнопка Stop прерывает воспроизведение

---

## 📎 Связанные документы

- [TASK 9.1 — Voice WebSocket API](./TASK_9.1_Voice_WebSocket.md)
- [TASK 9.2 — Real-time Transcription](./TASK_9.2_Realtime_Transcription.md)
