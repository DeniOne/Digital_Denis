"""
Digital Denis — Telegram Bot
═══════════════════════════════════════════════════════════════════════════

Telegram interface for Digital Denis.
"""

import os
import logging
from pathlib import Path
import tempfile

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Store session IDs per user
user_sessions: dict[int, str] = {}


# ═══════════════════════════════════════════════════════════════════════════
# Voice Transcription
# ═══════════════════════════════════════════════════════════════════════════

async def transcribe_voice(audio_path: Path) -> str:
    """Transcribe audio file using Groq Whisper."""
    
    if not GROQ_API_KEY:
        return "[Голосовые сообщения не настроены]"
    
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            files = {
                "file": (audio_path.name, f, "audio/ogg"),
                "model": (None, "whisper-large-v3"),
                "language": (None, "ru"),
            }
            
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files=files,
                timeout=60.0,
            )
            
            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                logger.error(f"Transcription failed: {response.text}")
                return "[Ошибка распознавания голоса]"


# ═══════════════════════════════════════════════════════════════════════════
# Backend Communication
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# Backend Communication
# ═══════════════════════════════════════════════════════════════════════════

async def send_to_backend(user: any, message: str) -> str:
    """Send message to backend and get response."""
    
    user_id = user.id
    session_id = user_sessions.get(user_id)
    
    payload = {
        "telegram_id": user_id,
        "username": user.username,
        "full_name": user.full_name or user.first_name,
        "content": message,
        "session_id": session_id,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/messages/telegram",
                json=payload,
                timeout=120.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                # Update session ID
                user_sessions[user_id] = data.get("session_id")
                return data.get("response", "Ошибка: нет ответа")
            else:
                logger.error(f"Backend error: {response.text}")
                return f"Ошибка сервера: {response.status_code}"
                
        except httpx.TimeoutException:
            return "Превышено время ожидания. Попробуйте позже."
        except httpx.ConnectError:
            return "Не удалось подключиться к серверу."
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Ошибка: {str(e)}"
            

# ═══════════════════════════════════════════════════════════════════════════
# Handlers
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я — Digital Denis, твой когнитивный партнёр.\n\n"
        "Можешь писать мне текст или отправлять голосовые сообщения.\n\n"
        "Команды:\n"
        "/start — начать заново\n"
        "/memory — последние воспоминания\n"
        "/help — справка"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "🧠 Digital Denis — Personal Cognitive Operating System\n\n"
        "Я помогаю структурировать мышление, сохранять решения "
        "и отслеживать когнитивные паттерны.\n\n"
        "Просто напиши мне своё сообщение или отправь голосовое.\n\n"
        "Особенности:\n"
        "• Сохраняю важные решения и инсайты\n"
        "• Применяю твой стиль мышления\n"
        "• Структурирую ответы\n\n"
        "Версия: 0.1.0 (MVP)"
    )


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /memory command."""
    # Memory command might need similar auth fix or we let it fail for now
    # Ideally should use telegram ID param if updated backend supports it
    await update.message.reply_text("Функция памяти временно обновляется.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user = update.effective_user
    
    # Send typing indicator
    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass
    
    # Get response from backend
    response = await send_to_backend(user, update.message.text)
    
    # Send response
    await update.message.reply_text(response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages."""
    user = update.effective_user
    
    # Download voice file
    voice_file = await update.message.voice.get_file()
    
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        await voice_file.download_to_drive(f.name)
        audio_path = Path(f.name)
    
    try:
        # Send typing indicator
        try:
            await update.message.chat.send_action("typing")
        except Exception:
            pass
        
        # Transcribe
        transcription = await transcribe_voice(audio_path)
        
        if transcription.startswith("["):
            # Error message
            await update.message.reply_text(transcription)
            return
        
        # Echo transcription
        await update.message.reply_text(f"🎤 Распознано: {transcription}")
        
        # Send typing indicator again
        try:
            await update.message.chat.send_action("typing")
        except Exception:
            pass
        
        # Get response from backend
        response = await send_to_backend(user, transcription)
        
        # Send response
        await update.message.reply_text(response)
        
    finally:
        # Cleanup
        audio_path.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Start polling
    print("🤖 Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
