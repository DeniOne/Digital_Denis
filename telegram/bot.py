"""
Digital Den — Telegram Bot
═══════════════════════════════════════════════════════════════════════════

Telegram interface for Digital Den.
"""

import os
import logging
import uuid
from pathlib import Path
from datetime import date, timedelta
import tempfile

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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

def get_stable_session_id(telegram_id: int) -> str:
    """Generate a stable UUID based on Telegram ID."""
    # Using a fixed namespace for Digital Den sessions
    NAMESPACE_DD = uuid.UUID('d3d1de1a-d3d1-4de1-a1d3-d3d1de1a2024')
    return str(uuid.uuid5(NAMESPACE_DD, f"tg_user_{telegram_id}"))


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

async def send_to_backend(user: any, message: str) -> dict:
    """Send message to backend and get response data."""
    
    user_id = user.id
    # Use stable session ID for Telegram by default to prevent context loss on bot restart
    session_id = user_sessions.get(user_id) or get_stable_session_id(user_id)
    
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
                return data
            else:
                logger.error(f"Backend error: {response.text}")
                return {"response": f"Ошибка сервера: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"response": "Превышено время ожидания. Попробуйте позже."}
        except httpx.ConnectError:
            return {"response": "Не удалось подключиться к серверу."}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"response": f"Ошибка: {str(e)}"}
            

# ═══════════════════════════════════════════════════════════════════════════
# Handlers
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я — Digital Den, твой когнитивный партнёр.\n\n"
        "Можешь писать мне текст или отправлять голосовые сообщения.\n\n"
        "Команды:\n"
        "/start — общее приветствие\n"
        "/reset — начать диалог заново\n"
        "/schedule — моё расписание\n"
        "/memory — последние воспоминания\n"
        "/search <запрос> — поиск в памяти\n"
        "/settings — мои настройки\n"
        "/help — справка"
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command — start a new session."""
    user = update.effective_user
    new_session_id = str(uuid.uuid4())
    user_sessions[user.id] = new_session_id
    await update.message.reply_text(
        "🧠 Контекст диалога очищен. Мы начали новую сессию.\n"
        "О чем хочешь поговорить?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "🧠 Digital Den — Personal Cognitive Operating System\n\n"
        "Я помогаю структурировать мышление, сохранять решения "
        "и отслеживать когнитивные паттерны.\n\n"
        "Просто напиши мне своё сообщение или отправь голосовое.\n\n"
        "🔍 **Работа с памятью:**\n"
        "• `/memory` — последние 10 записей\n"
        "• `/search <текст>` — поиск по всей памяти\n\n"
        "📅 **Расписание:**\n"
        "• 'Напомни позвонить маме завтра в 15:00'\n"
        "• 'Поставь встречу с клиентом на понедельник в 10:00'\n"
        "• 'Принимать таблетки 3 раза в день, 5 дней'\n"
        "• `/schedule` — список дел на сегодня\n\n"
        "⚙️ `/settings` — просмотр текущих настроек поведения ИИ.\n\n"
        "Версия: 0.2.1"
    )


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /memory command — show recent memories."""
    
    user = update.effective_user
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/memory",
                params={"telegram_id": user.id, "limit": 10},
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    await update.message.reply_text(
                        "🏜️ **Ваша цифровая память пока пуста.**\n\n"
                        "Продолжайте общаться со мной, и я буду автоматически сохранять "
                        "важные решения, выводы и факты.",
                        parse_mode="Markdown"
                    )
                    return
                
                # Format items
                text = "📁 **Последние воспоминания**\n\n"
                for item in items:
                    m_type = item.get("item_type", "thought")
                    content = item.get("content", "")
                    
                    emoji = {
                        "decision": "✅ [Решение]",
                        "insight": "💡 [Инсайт]",
                        "fact": "📌 [Факт]",
                        "thought": "💭 [Мысль]"
                    }.get(m_type, "•")
                    
                    # Shorten content for telegram
                    if len(content) > 150:
                        content = content[:147] + "..."
                        
                    text += f"{emoji}\n_{content}_\n\n"
                
                text += f"🔗 [Открыть полный проводник памяти]({BACKEND_URL.replace('8000', '3000')}/memory)"
                
                await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text("Не удалось загрузить воспоминания.")
                
        except Exception as e:
            logger.error(f"Memory load error: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке памяти.")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command — search in memory."""
    
    user = update.effective_user
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text(
            "🔎 **Поиск по памяти**\n\n"
            "Использование: `/search <ваш запрос>`\n"
            "Например: `/search проект Digital Den`",
            parse_mode="Markdown"
        )
        return
    
    # Send typing indicator
    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/memory/search",
                json={"query": query, "limit": 5, "telegram_id": user.id},
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    await update.message.reply_text(
                        f"🏜️ **Ничего не найдено по запросу: \"{query}\"**\n\n"
                        "Попробуйте изменить формулировку или проверьте настройки памяти.",
                        parse_mode="Markdown"
                    )
                    return
                
                # Format results
                text = f"🔎 **Результаты поиска: \"{query}\"**\n\n"
                for item in items:
                    m_type = item.get("item_type", "thought")
                    content = item.get("content", "")
                    relevance = item.get("relevance", 0)
                    
                    emoji = {
                        "decision": "✅ [Решение]",
                        "insight": "💡 [Инсайт]",
                        "fact": "📌 [Факт]",
                        "thought": "💭 [Мысль]"
                    }.get(m_type, "•")
                    
                    # Shorten content for telegram
                    if len(content) > 200:
                        content = content[:197] + "..."
                        
                    text += f"{emoji}\n_{content}_\n"
                    if relevance > 0:
                        text += f"🎯 Релевантность: {int(relevance * 100)}%\n"
                    text += "\n"
                
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                logger.error(f"Search error: {response.text}")
                await update.message.reply_text("Не удалось выполнить поиск. Попробуйте позже.")
                
        except Exception as e:
            logger.error(f"Search exception: {e}")
            await update.message.reply_text("Произошла ошибка при поиске.")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command — show current settings."""
    user = update.effective_user
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/settings",
                params={"telegram_id": user.id},
                timeout=30.0,
            )
            
            if response.status_code == 200:
                settings = response.json()
                
                # Extract sections
                behavior = settings.get("behavior", {})
                autonomy = settings.get("autonomy", {})
                
                text = "⚙️ **Настройки Digital Den**\n\n"
                
                text += "🤖 **Поведение:**\n"
                text += f"• Роль: `{behavior.get('ai_role', '—')}`\n"
                text += f"• Глубина: `{behavior.get('thinking_depth', '—')}`\n"
                text += f"• Стиль: `{behavior.get('response_style', '—')}`\n\n"
                
                text += "⚡ **Автономия:**\n"
                text += f"• Инициатива: `{autonomy.get('initiative_level', '—')}`\n"
                text += f"• Частота: `{autonomy.get('intervention_frequency', '—')}`\n\n"
                
                text += f"🔗 [Настроить всё в веб-интерфейсе]({BACKEND_URL.replace('8000', '3000')}/settings)"
                
                await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text("Не удалось загрузить настройки.")
                
        except Exception as e:
            logger.error(f"Settings load error: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке настроек.")


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command — show today's schedule."""
    
    user = update.effective_user
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/schedule/today",
                params={"telegram_id": user.id},
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    await update.message.reply_text(
                        "📅 **Расписание на сегодня**\n\n"
                        "Нет запланированных дел!",
                        parse_mode="Markdown"
                    )
                    return
                
                # Format items
                text = "📅 **Расписание на сегодня**\n\n"
                for item in items:
                    item_type = item.get("item_type", "reminder")
                    title = item.get("title", "")
                    time_str = item.get("start_at", item.get("due_at", ""))
                    status = item.get("status", "pending")
                    
                    emoji = {"event": "📌", "task": "📝", "reminder": "🔔"}.get(item_type, "•")
                    status_emoji = "✅" if status == "completed" else ""
                    
                    text += f"{emoji} {status_emoji}{title}\n"
                    if time_str:
                        text += f"   ⏰ {time_str}\n"
                    text += "\n"
                
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                await update.message.reply_text("Не удалось загрузить расписание.")
                
        except Exception as e:
            logger.error(f"Schedule load error: {e}")
            await update.message.reply_text(
                "📅 Расписание пока пустое.\n\n"
                "Скажи мне что-то вроде:\n"
                "• 'Напомни позвонить маме в 15:00'\n"
                "• 'Поставь встречу на завтра в 10:00'"
            )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user = update.effective_user
    
    # Send typing indicator
    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass
    
    # Get response from backend
    data = await send_to_backend(user, update.message.text)
    response_text = data.get("response", "Ошибка: нет ответа")
    metadata = data.get("metadata")
    
    # Check for schedule confirmation metadata
    reply_markup = None
    if metadata and metadata.get("item_id"):
        item_id = metadata["item_id"]
        # Standard buttons for schedule items
        keyboard = [
            [
                InlineKeyboardButton("✅ Выполнено", callback_data=f"reminder:done:{item_id}"),
                InlineKeyboardButton("⏰ +15 мин", callback_data=f"reminder:snooze:{item_id}"),
            ],
            [
                InlineKeyboardButton("❌ Пропустить", callback_data=f"reminder:skip:{item_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send response
    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")


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
        data = await send_to_backend(user, transcription)
        response_text = data.get("response", "Ошибка: нет ответа")
        metadata = data.get("metadata")
        
        # Check for schedule confirmation metadata
        reply_markup = None
        if metadata and metadata.get("item_id"):
            item_id = metadata["item_id"]
            keyboard = [
                [
                    InlineKeyboardButton("✅ Выполнено", callback_data=f"reminder:done:{item_id}"),
                    InlineKeyboardButton("⏰ +15 мин", callback_data=f"reminder:snooze:{item_id}"),
                ],
                [
                    InlineKeyboardButton("❌ Пропустить", callback_data=f"reminder:skip:{item_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        # Send response
        await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="Markdown")
        
    finally:
        # Cleanup
        audio_path.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# Reminder Callback Handlers
# ═══════════════════════════════════════════════════════════════════════════

async def handle_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder inline button callbacks."""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith("reminder:"):
        return
    
    parts = data.split(":")
    if len(parts) < 3:
        return
    
    action = parts[1]  # done, snooze, skip
    instance_id = parts[2]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/reminders/{instance_id}/{action}",
                timeout=10.0,
            )
            
            if response.status_code == 200:
                if action == "done":
                    await query.edit_message_text(
                        f"{query.message.text}\n\n✅ Выполнено!"
                    )
                elif action == "snooze":
                    await query.edit_message_text(
                        f"{query.message.text}\n\n⏰ Отложено на 15 минут"
                    )
                elif action == "skip":
                    await query.edit_message_text(
                        f"{query.message.text}\n\n❌ Пропущено"
                    )
            else:
                await query.edit_message_text(
                    f"{query.message.text}\n\n⚠️ Ошибка обработки"
                )
                
        except Exception as e:
            logger.error(f"Reminder callback error: {e}")
            await query.edit_message_text(
                f"{query.message.text}\n\n⚠️ Ошибка соединения"
            )


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
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CallbackQueryHandler(handle_reminder_callback, pattern="^reminder:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Start polling
    print("🤖 Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

