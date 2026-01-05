"""
Digital Den — Nightly Kaizen Worker
═══════════════════════════════════════════════════════════════════════════

Runs nightly to:
1. Create Kaizen snapshots for all active users.
2. Generate deep AI insights using Gemini CLI.
3. Save results to the database.
"""

import asyncio
from typing import List
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import async_session_maker
from core.logging import get_logger
from analytics.kaizen_service import KaizenEngine
from llm.llm_selector import llm_selector, ModelRole, LLMMessage
from memory.models import User

logger = get_logger(__name__)

class KaizenWorker:
    def __init__(self):
        self.target_date = date.today() - timedelta(days=1)
        
    async def run(self):
        """Main entry point for the worker."""
        logger.info("kaizen_worker_started", target_date=self.target_date.isoformat())
        
        async with async_session_maker() as session:
            # 1. Get all active users
            users = await self._get_active_users(session)
            logger.info("kaizen_worker_users_found", count=len(users))
            
            engine = KaizenEngine(session)
            
            for user in users:
                try:
                    # 2. Create daily snapshot (calculates metrics)
                    snapshot = await engine.create_daily_snapshot(user.id, self.target_date)
                    logger.info("kaizen_snapshot_created", user_id=user.id, index=snapshot.kaizen_index)
                    
                    # 3. Deep AI Analysis via Gemini CLI
                    await self._generate_deep_insight(session, user, snapshot)
                    
                except Exception as e:
                    logger.error("kaizen_worker_user_failed", user_id=user.id, error=str(e))
                    continue
        
        logger.info("kaizen_worker_finished")

    async def _get_active_users(self, session: AsyncSession) -> List[User]:
        """Fetch users who were active recently."""
        # Simple implementation: all active users
        stmt = select(User).where(User.is_active == True)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _generate_deep_insight(self, session: AsyncSession, user: User, snapshot):
        """Generate personalized insights using Gemini CLI."""
        
        # Prepare data for AI
        prompt = f"""Проанализируй данные Kaizen для пользователя {user.username} за {self.target_date}.
        
Индекс Kaizen: {snapshot.kaizen_index:.2f} (изменение: {snapshot.kaizen_index_7d:.2f} за неделю)
Состояние: {snapshot.user_state}
Контуры:
- Когнитивный: {snapshot.cognitive_score:.2f} (тренд: {snapshot.cognitive_trend})
- Решенческий: {snapshot.decision_score:.2f} (тренд: {snapshot.decision_trend})
- Системность: {snapshot.management_score:.2f} (тренд: {snapshot.management_trend})
- Устойчивость: {snapshot.stability_score:.2f} (тренд: {snapshot.stability_trend})

Активность:
- Сообщений: {snapshot.messages_count}
- Решений: {snapshot.decisions_count}
- Инсайтов: {snapshot.insights_count}

Зеркальное наблюдение: {snapshot.mirror_observation}

ЗАДАЧА:
Сделай глубокий разбор (reasoning). Почему индекс такой? Какие скрытые паттерны ты видишь?
Дай одну конкретную рекомендацию на завтра в стиле "Digital Soul".

Формат ответа:
ПОЧЕМУ: (кратко)
ИНСАЙТ: (глубоко)
РЕКОМЕНДАЦИЯ: (действие)
"""

        messages = [
            LLMMessage(role="system", content="Ты — Digital Soul, ядро системы Digital Den. Твоя цель — глубокая помощь в саморазвитии."),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            # Используем роль GEMINI_CLI для вызова консольного интерфейса
            response = await llm_selector.complete(
                role=ModelRole.GEMINI_CLI,
                messages=messages,
                temperature=0.7
            )
            
            # Сохраняем инсайт в лог или БД (в будущем в специальную таблицу)
            logger.info("kaizen_deep_insight", user_id=user.id, insight=response.content[:100] + "...")
            
            # TODO: Сохранение в таблицу KaizenInsight при наличии соответствующей модели в БД
            
        except Exception as e:
            logger.error("kaizen_insight_failed", user_id=user.id, error=str(e))

if __name__ == "__main__":
    worker = KaizenWorker()
    asyncio.run(worker.run())
