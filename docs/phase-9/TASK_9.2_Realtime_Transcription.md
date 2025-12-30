# 🎤 TASK 9.2 — Real-time Transcription

**Проект:** Digital Denis v0.2.0  
**Проект:** Digital Denis v0.2.0  
**Статус:** ✅ Завершено  
**Приоритет:** Высокий  
**Оценка:** 2-3 дня  
**Зависимости:** TASK 9.1

---

## 🎯 Цель

Реализовать транскрипцию речи в реальном времени на фронтенде с отправкой на WebSocket.

---

## 📋 Чеклист реализации

### Frontend Audio Capture
- [x] Запрос разрешения на микрофон
- [x] MediaRecorder API для записи
- [x] Формат: WebM/Opus (оптимально для Whisper)
- [x] Настраиваемый bitrate
- [x] Обработка ошибок доступа к микрофону

### Streaming
- [x] Отправка audio chunks по WebSocket
- [x] Интервал отправки (каждые 250-500ms)
- [x] Индикатор "recording" в UI
- [x] Кнопки Start/Stop/Pause

### Real-time Display
- [x] Отображение частичной транскрипции
- [x] Анимация "typing" во время обработки
- [x] Финальный текст по завершении
- [x] История голосовых сообщений

### Backend Groq Integration
- [x] Буферизация chunks на сервере (Task 9.1)
- [x] Вызов Groq Whisper API (Task 9.1)
- [x] Streaming partial results (через последовательные транскрипции)
- [x] Fallback на batch при ошибках

### Error Handling
- [x] Reconnect при потере WebSocket
- [x] Retry логика для транскрипции
- [x] Graceful degradation
- [x] User-friendly error messages

---

## 📦 Артефакты

```
frontend/
└── src/
    ├── hooks/
    │   ├── useVoiceRecorder.ts     # MediaRecorder hook
    │   └── useVoiceWebSocket.ts    # WebSocket hook
    ├── components/
    │   ├── VoiceButton.tsx         # Record button
    │   ├── VoiceWaveform.tsx       # Audio visualizer
    │   └── TranscriptDisplay.tsx   # Live transcript
    └── lib/
        └── audio/
            ├── recorder.ts         # Audio recording logic
            └── processor.ts        # Audio processing

backend/
└── voice/
    └── groq_whisper.py             # Groq Whisper client
```

---

## 📝 Пример Hook для записи

```typescript
// hooks/useVoiceRecorder.ts
import { useState, useRef, useCallback } from 'react';

export function useVoiceRecorder(onDataAvailable: (blob: Blob) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  
  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000,
      }
    });
    
    mediaRecorder.current = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 16000,
    });
    
    mediaRecorder.current.ondataavailable = (e) => {
      if (e.data.size > 0) {
        onDataAvailable(e.data);
      }
    };
    
    // Send chunks every 500ms
    mediaRecorder.current.start(500);
    setIsRecording(true);
  }, [onDataAvailable]);
  
  const stopRecording = useCallback(() => {
    mediaRecorder.current?.stop();
    mediaRecorder.current?.stream.getTracks().forEach(t => t.stop());
    setIsRecording(false);
  }, []);
  
  return { isRecording, startRecording, stopRecording };
}
```

---

## 📊 Latency Budget

| Step | Target | Max |
|------|--------|-----|
| Audio chunk capture | — | 500ms |
| WebSocket send | <50ms | 100ms |
| Groq Whisper API | <200ms | 500ms |
| WebSocket receive | <50ms | 100ms |
| **Total** | **<300ms** | **700ms** |

---

## ✅ Критерии завершения

- [ ] Запись работает на Chrome/Safari/Firefox
- [ ] Транскрипция появляется в реальном времени
- [ ] Latency < 700ms end-to-end
- [ ] Корректная обработка ошибок

---

## 📎 Связанные документы

- [TASK 9.1 — Voice WebSocket API](./TASK_9.1_Voice_WebSocket.md)
- [TASK 9.3 — Voice Response (TTS)](./TASK_9.3_Voice_TTS.md)
