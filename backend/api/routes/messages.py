"""
Digital Den — Messages API Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for message handling.
"""

from typing import Optional
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.database import get_db, AsyncSession
from orchestrator.router import router as request_router
from memory.short_term import short_term_memory
from core.auth import get_current_user, get_current_user_optional
from memory.models import User
from agents.core_agent import core_agent


router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class MessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    response: str
    agent: str
    session_id: str
    memory_saved: bool = False
    tokens_used: int = 0
    metadata: Optional[dict] = None


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post("", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Send message to Digital Den.
    
    Returns agent response with metadata.
    """
    # Parse session ID
    session_id = None
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
        except ValueError:
            pass
    
    # Route via RAG 2.0 Universal Core (with fallback)
    try:
        # RAG 2.0 imports (lazy loading)
        from orchestrator.rag2_orchestrator import rag2_orchestrator
        from agents.core_agent import core_agent
        from agents.base import AgentContext
        
        # Get conversation ID
        # Handle anonymous users (current_user can be None)
        if current_user and current_user.id:
            user_id = current_user.id
            if current_user.telegram_id:
                # [Fix] Use telegram_id (as string) for conversation_id to sync with Telegram history
                conversation_id = str(current_user.telegram_id)
            else:
                # Legacy behavior: use session_id or user_id
                conversation_id = str(session_id) if session_id else str(user_id)
        else:
            # Anonymous user - handle session_id carefully
            try:
                # If session_id is a valid UUID, use it as user_id for consistency
                if session_id:
                    user_id = UUID(session_id)
                else:
                    user_id = UUID("00000000-0000-0000-0000-000000000000")
            except:
                # session_id is not a valid UUID, generate one or use a fixed one
                user_id = uuid4()
            
            conversation_id = str(session_id) if session_id else str(user_id)
        
        # Get recent messages from short-term memory
        recent_messages = await short_term_memory.get_chat_history(conversation_id)
        formatted_messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in recent_messages[-5:]
        ]
        
        # RAG 2.0 Orchestration
        rag_result = await rag2_orchestrator.process_message(
            db=db,
            user_id=user_id,
            chat_id=conversation_id,
            message=request.content,
            recent_messages=formatted_messages,
            user_settings=None
        )
        
        # Prepare context for core agent
        # ВАЖНО: не передаём весь framed_context в system_prompt (слишком большой)
        # Вместо этого передаём только первые 3000 символов
        context_preview = rag_result["framed_context"][:3000]
        
        agent_context = AgentContext(
            user_message=request.content,
            user_id=user_id,  # используем переменную user_id (может быть anonymous)
            session_id=session_id or conversation_id,
            system_prompt=f"[RAG 2.0 Context Preview]\n{context_preview}\n\n[Full context truncated for performance]",
            memories=[],
            history=formatted_messages,
            db=db,  # Нужно для schedule_agent
        )
        
        # Выбор агента на основе intent из RAG 2.0
        detected_intent = rag_result.get("intent", "general")
        
        if detected_intent == "schedule":
            # Напоминания, события, задачи — используем schedule_agent
            from agents.schedule_agent import schedule_agent
            llm_response = await schedule_agent.process(agent_context)
        elif detected_intent == "memory":
            # Запросы о памяти — используем memory_agent
            from agents.memory_agent import memory_agent
            llm_response = await memory_agent.process(agent_context)
        elif detected_intent == "analysis":
            # Аналитика — используем analyst_agent
            from agents.analyst_agent import analyst_agent
            llm_response = await analyst_agent.process(agent_context)
        else:
            # Всё остальное — core_agent
            llm_response = await core_agent.process(agent_context)
        
        # Save to short-term memory
        await short_term_memory.add_message(
            session_id=conversation_id,
            role="user",
            content=request.content
        )
        await short_term_memory.add_message(
            session_id=conversation_id,
            role="assistant",
            content=llm_response.content,
            agent=llm_response.agent
        )
        
        # Save to long-term memory if important
        if llm_response.save_to_memory:
            from memory.long_term import long_term_memory
            from memory.embeddings import embedding_service
            
            # Safe UUID conversion for source_session
            valid_session_uuid = None
            if conversation_id:
                try:
                    valid_session_uuid = UUID(conversation_id)
                except:
                    # If it's not a UUID, checking if it's a telegram ID
                    if current_user and current_user.telegram_id and str(current_user.telegram_id) == conversation_id:
                        valid_session_uuid = uuid5(NAMESPACE_DNS, f"telegram_{conversation_id}")
                    else:
                        pass
            
            # Сохранить exchange (user + assistant) как decision/insight
            saved_item = await long_term_memory.save(
                db=db,
                user_id=user_id,
                item_type=llm_response.memory_type or "insight",
                content=f"Q: {request.content}\nA: {llm_response.content}",
                summary=None,
                confidence=llm_response.confidence,
                source_agent=llm_response.agent,
                source_session=valid_session_uuid
            )
            
            # Создать embeddings для нового элемента (критически важно для поиска!)
            try:
                await embedding_service.index_items(db, [saved_item.id])
            except Exception as emb_err:
                print(f"⚠️ Embedding indexing failed: {emb_err}")
        
        return MessageResponse(
            response=llm_response.content,
            agent=f"RAG2.0-{llm_response.agent or 'Core'}",
            session_id=str(session_id or conversation_id),
            memory_saved=llm_response.save_to_memory,
            tokens_used=llm_response.tokens_used,
            metadata=llm_response.memory_data,
        )
        
    except Exception as e:
        import traceback
        print(f"⚠️ RAG 2.0 Error, falling back to classic router: {e}")
        print(traceback.format_exc())
        
        # Fallback to classic request router
        try:
            response = await request_router.route(
                user_message=request.content,
                session_id=session_id,
                db=db,
                user_id=current_user.id,
            )
            
            return MessageResponse(
                response=response.content,
                agent=f"{response.agent} (fallback)",
                session_id=str(response.follow_up) if response.follow_up else str(session_id or ""),
                memory_saved=response.save_to_memory,
                tokens_used=response.tokens_used,
            )
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=str(e))


class TelegramMessageRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    content: str
    session_id: Optional[str] = None


@router.post("/telegram", response_model=MessageResponse)
async def send_telegram_message(
    request: TelegramMessageRequest,
    db: AsyncSession = Depends(get_db),
    # Secure this endpoint: Only the bot (possessing the token) can call it.
    # In production, specific IP whitelisting or a shared secret is better.
    # Here we can check a header or simply rely on the fact that this is an internal API.
    # But for safety, let's verify a header potentially.
):
    """
    Handle message explicitly from Telegram Bot.
    Auto-creates user if not exists.
    """
    import os
    from sqlalchemy import select
    from core.config import settings
    
    # ═══════════════════════════════════════════════════════════════════════
    # ACCESS CONTROL - Only whitelisted Telegram IDs can use the system
    # ═══════════════════════════════════════════════════════════════════════
    allowed_ids_str = os.getenv("ALLOWED_TELEGRAM_IDS", "")
    if allowed_ids_str:
        allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        if request.telegram_id not in allowed_ids:
            raise HTTPException(
                status_code=403,
                detail="Доступ запрещён. Ваш Telegram ID не в белом списке."
            )
    
    # 1. Find or Create User
    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=request.telegram_id,
            username=request.username,
            full_name=request.full_name,
            role="owner"  # Default role
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    
    # 2. Parse Session
    session_id = None
    if request.session_id:
        try:
            session_id = UUID(request.session_id)
        except ValueError:
            pass
    
    # 3. Process Message via RAG 2.0 (with fallback)
    try:
        # RAG 2.0 imports (lazy loading)
        from orchestrator.rag2_orchestrator import rag2_orchestrator
        from agents.core_agent import core_agent
        from agents.base import AgentContext
        
        # Get recent messages from short-term memory
        chat_id = str(request.telegram_id)
        recent_messages = await short_term_memory.get_chat_history(chat_id)
        
        # Convert to format expected by RAG 2.0
        formatted_messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in recent_messages[-5:]  # последние 5
        ]
        
        # Load UserSettings for this user (важно для персонализации!)
        from sqlalchemy import select
        from memory.models import UserSettings as UserSettingsModel
        user_settings_result = await db.execute(
            select(UserSettingsModel).where(UserSettingsModel.user_id == user.id)
        )
        user_settings = user_settings_result.scalar_one_or_none()
        
        # RAG 2.0 Orchestration
        rag_result = await rag2_orchestrator.process_message(
            db=db,
            user_id=user.id,
            chat_id=chat_id,
            message=request.content,
            recent_messages=formatted_messages,
            user_settings=user_settings  # Теперь передаём настройки!
        )
        
        # Prepare context for core agent (with truncation)
        context_preview = rag_result["framed_context"][:3000]
        
        # Создаём детерминированный UUID для session на основе telegram_id
        from uuid import uuid5, NAMESPACE_DNS
        deterministic_session_uuid = uuid5(NAMESPACE_DNS, f"telegram_{chat_id}")
        
        # Системный промпт с информацией о памяти RAG 2.0
        system_prompt = f"""Ты — Digital Denis, персональный AI-ассистент с ДОЛГОВРЕМЕННОЙ ПАМЯТЬЮ.

ВАЖНО: У тебя ЕСТЬ доступ к долговременной памяти пользователя через систему RAG 2.0.
Информация ниже — это релевантные воспоминания, извлечённые из базы данных.
Используй эту информацию в ответах. НЕ ГОВОРИ, что у тебя нет памяти — это неправда.

{context_preview}

Если в контексте выше есть информация о целях, решениях или инсайтах пользователя — 
активно используй её и ссылайся на неё в ответах.
"""
        
        agent_context = AgentContext(
            session_id=chat_id,
            user_message=request.content,
            system_prompt=system_prompt,
            memories=[], # уже в framed_context
            history=formatted_messages,
            db=db,  # Нужно для schedule_agent
            user_id=user.id, # Исправлено: передаем user_id
        )
        
        # Выбор агента на основе intent из RAG 2.0
        detected_intent = rag_result.get("intent", "general")
        
        # DEBUG: Log detected intent
        logger.info(f"🔍 DEBUG: detected_intent = '{detected_intent}' for message: {content[:50]}")
        
        if detected_intent == "schedule":
            # Напоминания, события, задачи — используем schedule_agent
            from agents.schedule_agent import schedule_agent
            llm_response = await schedule_agent.process(agent_context)
        elif detected_intent == "memory":
            # Запросы о памяти — используем memory_agent
            from agents.memory_agent import memory_agent
            llm_response = await memory_agent.process(agent_context)
        elif detected_intent == "analysis":
            # Аналитика — используем analyst_agent
            from agents.analyst_agent import analyst_agent
            llm_response = await analyst_agent.process(agent_context)
        else:
            # Всё остальное — core_agent
            llm_response = await core_agent.process(agent_context)
        
        # Save to short-term memory
        await short_term_memory.add_message(
            session_id=chat_id,
            role="user",
            content=request.content
        )
        await short_term_memory.add_message(
            session_id=chat_id,
            role="assistant",
            content=llm_response.content,
            agent=llm_response.agent
        )
        
        # Save to long-term memory if important
        if llm_response.save_to_memory:
            from memory.long_term import long_term_memory
            from memory.embeddings import embedding_service
            
            # Сохранить exchange (user + assistant) как decision/insight
            saved_item = await long_term_memory.save(
                db=db,
                user_id=user.id,
                item_type=llm_response.memory_type or "insight",
                content=f"Q: {request.content}\nA: {llm_response.content}",
                summary=None,
                confidence=llm_response.confidence,
                source_agent=llm_response.agent,
                source_session=deterministic_session_uuid  # Теперь всегда валидный UUID!
            )
            
            # Создать embeddings для нового элемента (критически важно для поиска!)
            try:
                await embedding_service.index_items(db, [saved_item.id])
            except Exception as emb_err:
                print(f"⚠️ Embedding indexing failed: {emb_err}")
            
        # Final commit for all changes (user, state, items, memories, embeddings)
        await db.commit()
        
        return MessageResponse(
            response=llm_response.content,
            agent=f"RAG2.0-{llm_response.agent or 'Core'}",
            session_id=str(session_id or deterministic_session_uuid),
            memory_saved=llm_response.save_to_memory,
            tokens_used=llm_response.tokens_used,
            metadata=llm_response.memory_data,
        )
        
    except Exception as e:
        import traceback
        print(f"⚠️ RAG 2.0 Telegram Error, falling back to classic router: {e}")
        print(traceback.format_exc())
        
        # Fallback to classic request router
        try:
            response = await request_router.route(
                user_message=request.content,
                session_id=str(session_id or chat_id),
                db=db,
                user_id=user.id,
            )
            
            # Commit any changes from fallback (or previous steps)
            await db.commit()
            
            return MessageResponse(
                response=response.content,
                agent=f"{response.agent} (tg-fallback)",
                session_id=str(response.follow_up) if response.follow_up else str(session_id or chat_id),
                memory_saved=response.save_to_memory,
                tokens_used=response.tokens_used,
            )
        except Exception as fallback_error:
            print(f"❌ TG Fallback also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=str(fallback_error))


@router.get("/session/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user_optional),
):
    """
    Get chat history for session.
    """
    print(f"DEBUG: get_session_history requested for {session_id}")
    print(f"DEBUG: current_user = {current_user}")
    if current_user:
        print(f"DEBUG: current_user.id = {current_user.id}")
        print(f"DEBUG: current_user.telegram_id = {current_user.telegram_id}")
    else:
        print("DEBUG: current_user is None")

    target_session_id = session_id
    
    # If user is logged in and has telegram_id, use that for history
    if current_user and current_user.telegram_id:
        target_session_id = str(current_user.telegram_id)
        print(f"DEBUG: Redirecting session {session_id} -> {target_session_id}")
        
    history = await short_term_memory.get_chat_history(target_session_id)
    
    return {"session_id": target_session_id, "messages": history}
