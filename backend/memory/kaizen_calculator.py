"""
Digital Den — Kaizen Metrics Calculator
═══════════════════════════════════════════════════════════════════════════

Расчёт метрик качества мышления пользователя.
"""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem, KaizenMetric


class KaizenMetricsCalculator:
    """
    Расчёт Kaizen метрик для пользователя.
    
    Dimensions:
    - decision_quality: процент положительных исходов решений
    - consistency: стабильность использования принципов
    - clarity_of_thought: рост confidence_level новых воспоминаний
    - execution: соотношение завершённых задач
    - emotional_stability: стабильность эмоциональных записей
    """
    
    async def calculate_decision_quality(
        self,
        db: AsyncSession,
        user_id: UUID,
        period_days: int = 30
    ) -> float:
        """
        Рассчитать decision_quality: процент положительных исходов решений.
        
        Returns:
            float: 0.0 - 100.0
        """
        since = datetime.utcnow() - timedelta(days=period_days)
        
        stmt = select(MemoryItem).where(
            MemoryItem.user_id == user_id,
            MemoryItem.item_type == "decision",
            MemoryItem.created_at >= since,
            MemoryItem.usage_count > 0
        )
        result = await db.execute(stmt)
        decisions = result.scalars().all()
        
        if not decisions:
            return 50.0  # Нейтральный скор если нет данных
        
        total_outcomes = sum(d.positive_outcomes + d.negative_outcomes for d in decisions)
        positive = sum(d.positive_outcomes for d in decisions)
        
        if total_outcomes == 0:
            return 50.0
        
        quality = (positive / total_outcomes) * 100
        return round(quality, 2)
    
    async def calculate_consistency(
        self,
        db: AsyncSession,
        user_id: UUID,
        period_days: int = 30
    ) -> float:
        """
        Рассчитать consistency: как часто используются принципы.
        
        Returns:
            float: 0.0 - 100.0
        """
        since = datetime.utcnow() - timedelta(days=period_days)
        
        # Количество принципов с usage_count > 0
        stmt = select(MemoryItem).where(
            MemoryItem.user_id == user_id,
            MemoryItem.item_type == "principle",
            MemoryItem.created_at >= since
        )
        result = await db.execute(stmt)
        principles = result.scalars().all()
        
        if not principles:
            return 50.0
        
        used_principles = [p for p in principles if p.usage_count > 0]
        
        consistency = (len(used_principles) / len(principles)) * 100
        return round(consistency, 2)
    
    async def calculate_clarity_of_thought(
        self,
        db: AsyncSession,
        user_id: UUID,
        period_days: int = 30
    ) -> float:
        """
        Рассчитать clarity_of_thought: процент воспоминаний с high confidence.
        
        Returns:
            float: 0.0 - 100.0
        """
        since = datetime.utcnow() - timedelta(days=period_days)
        
        stmt = select(MemoryItem).where(
            MemoryItem.user_id == user_id,
            MemoryItem.created_at >= since,
            MemoryItem.item_type.in_(["fact", "decision", "insight"])
        )
        result = await db.execute(stmt)
        memories = result.scalars().all()
        
        if not memories:
            return 50.0
        
        high_confidence = [m for m in memories if m.confidence_level == "high"]
        
        clarity = (len(high_confidence) / len(memories)) * 100
        return round(clarity, 2)
    
    async def calculate_execution(
        self,
        db: AsyncSession,
        user_id: UUID,
        period_days: int = 30
    ) -> float:
        """
        Рассчитать execution: процент задач с положительным исходом.
        
        Returns:
            float: 0.0 - 100.0
        """
        since = datetime.utcnow() - timedelta(days=period_days)
        
        stmt = select(MemoryItem).where(
            MemoryItem.user_id == user_id,
            MemoryItem.item_type == "task",
            MemoryItem.created_at >= since
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        if not tasks:
            return 50.0
        
        completed_tasks = [t for t in tasks if t.positive_outcomes > 0 or t.status == "archived"]
        
        execution_rate = (len(completed_tasks) / len(tasks)) * 100
        return round(execution_rate, 2)
    
    async def save_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        dimension: str,
        score: float,
        context: str = None
    ):
        """
        Сохранить метрику в базу.
        
        Args:
            db: Database session
            user_id: ID пользователя
            dimension: Название метрики
            score: Значение (0.0 - 100.0)
            context: Контекст (опционально)
        """
        metric = KaizenMetric(
            user_id=user_id,
            dimension=dimension,
            score=score,
            context=context
        )
        db.add(metric)
        await db.commit()
    
    async def calculate_all_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        period_days: int = 30
    ):
        """
        Рассчитать и сохранить все метрики для пользователя.
        
        Args:
            db: Database session
            user_id: ID пользователя
            period_days: Период для расчёта (дни)
        """
        # Decision Quality
        decision_quality = await self.calculate_decision_quality(db, user_id, period_days)
        await self.save_metrics(db, user_id, "decision_quality", decision_quality, f"Last {period_days} days")
        
        # Consistency
        consistency = await self.calculate_consistency(db, user_id, period_days)
        await self.save_metrics(db, user_id, "consistency", consistency, f"Last {period_days} days")
        
        # Clarity of Thought
        clarity = await self.calculate_clarity_of_thought(db, user_id, period_days)
        await self.save_metrics(db, user_id, "clarity_of_thought", clarity, f"Last {period_days} days")
        
        # Execution
        execution = await self.calculate_execution(db, user_id, period_days)
        await self.save_metrics(db, user_id, "execution", execution, f"Last {period_days} days")
        
        print(f"[Kaizen] Calculated metrics for user {user_id}: decision_quality={decision_quality}, consistency={consistency}, clarity={clarity}, execution={execution}")


# Global instance
kaizen_calculator = KaizenMetricsCalculator()
