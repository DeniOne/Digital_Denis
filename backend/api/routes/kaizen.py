"""
Digital Den — Kaizen Engine API Routes
═══════════════════════════════════════════════════════════════════════════

API endpoints for Kaizen Engine — personal development tracking.

Based on: docs/kaizen_engine.md
"""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from analytics.kaizen_service import KaizenEngine
from core.auth import get_current_user_optional


router = APIRouter(prefix="/kaizen", tags=["Kaizen Engine"])

# Test user ID for local development
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


# ═══════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════

class KaizenIndexResponse(BaseModel):
    """Kaizen index with relative dynamics."""
    kaizen_index: float = Field(..., description="Относительное изменение")
    change_7d: float = Field(..., description="Изменение за 7 дней")
    change_14d: float = Field(..., description="Изменение за 14 дней")
    change_30d: float = Field(..., description="Изменение за 30 дней")
    user_state: str = Field(..., description="Текущее состояние")
    state_label: str = Field(..., description="Метка состояния")


class ContourResponse(BaseModel):
    """Single Kaizen contour data."""
    contour: str = Field(..., description="Идентификатор контура")
    name: str = Field(..., description="Название контура")
    description: str = Field(..., description="Описание контура")
    score: float = Field(..., description="Текущий показатель (0-1)")
    trend: str = Field(..., description="Направление тренда")
    change_pct: float = Field(..., description="Процент изменения")
    icon: str = Field(..., description="Иконка контура")


class ContoursResponse(BaseModel):
    """All 4 Kaizen contours."""
    contours: List[ContourResponse]


class MirrorResponse(BaseModel):
    """Kaizen Mirror observations."""
    observations: List[str] = Field(..., description="Наблюдения (нейтральный язык)")


class HistoryPoint(BaseModel):
    """Single point in Kaizen history."""
    date: str
    kaizen_index: float
    user_state: str
    cognitive: float
    decision: float
    management: float
    stability: float


class HistoryResponse(BaseModel):
    """Kaizen history for charts."""
    history: List[HistoryPoint]


class UserStateForAIResponse(BaseModel):
    """User state for Adaptive AI Behavior."""
    state: str
    confidence: float
    kaizen_index: Optional[float] = None
    contours: dict
    recommendations: dict


# ═══════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/index", response_model=KaizenIndexResponse)
async def get_kaizen_index(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Получить текущий Kaizen-индекс пользователя.
    
    Возвращает относительную динамику развития:
    - kaizen_index: агрегированное изменение
    - change_7d/14d/30d: изменение за периоды
    - user_state: текущее состояние (growth/plateau/fluctuation/overload)
    """
    engine = KaizenEngine(session)
    result = await engine.get_current_kaizen_index(current_user.id)
    return KaizenIndexResponse(**result)


@router.get("/contours", response_model=ContoursResponse)
async def get_kaizen_contours(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Получить все 4 контура Kaizen.
    
    Контуры:
    - cognitive (Когнитивный) — ясность мышления
    - decision (Решенческий) — качество решений
    - management (Системность) — структурность мышления
    - stability (Устойчивость) — психокогнитивная стабильность
    """
    engine = KaizenEngine(session)
    contours = await engine.get_contours(current_user.id)
    return ContoursResponse(contours=[ContourResponse(**c) for c in contours])


@router.get("/mirror", response_model=MirrorResponse)
async def get_kaizen_mirror(
    limit: int = Query(default=3, ge=1, le=10),
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Получить наблюдения Kaizen-зеркала.
    
    Зеркало отражает:
    - Нейтральные наблюдения (без оценок)
    - Динамику мышления (не вердикт)
    - 1-2 предложения каждое
    
    Язык: "наблюдается", "зафиксировано", "изменилось"
    """
    engine = KaizenEngine(session)
    observations = await engine.get_kaizen_mirror(current_user.id, limit)
    return MirrorResponse(observations=observations)


@router.get("/history", response_model=HistoryResponse)
async def get_kaizen_history(
    days: int = Query(default=30, ge=7, le=90),
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Получить историю Kaizen-индекса для графиков.
    
    Возвращает данные за указанное количество дней.
    """
    engine = KaizenEngine(session)
    history = await engine.get_history(current_user.id, days)
    return HistoryResponse(history=[HistoryPoint(**h) for h in history])


@router.get("/state-for-ai", response_model=UserStateForAIResponse)
async def get_user_state_for_ai(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Получить состояние пользователя для Adaptive AI Behavior.
    
    Используется оркестратором для адаптации поведения ИИ.
    
    Возвращает рекомендации:
    - behavior_mode: режим поведения (strategist/analyst/coach/fixer)
    - thinking_depth: глубина мышления (shallow/structured/deep)
    - response_length: длина ответа (brief/medium/detailed)
    """
    engine = KaizenEngine(session)
    result = await engine.get_user_state_for_ai(current_user.id)
    return UserStateForAIResponse(**result)


@router.post("/snapshot")
async def create_kaizen_snapshot(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Создать ежедневный снимок Kaizen (для тестирования).
    
    В production этот endpoint вызывается background worker'ом.
    """
    engine = KaizenEngine(session)
    snapshot = await engine.create_daily_snapshot(current_user.id)
    
    return {
        "id": str(snapshot.id),
        "date": snapshot.snapshot_date.isoformat(),
        "kaizen_index": snapshot.kaizen_index,
        "user_state": snapshot.user_state,
        "mirror": snapshot.mirror_observation,
    }
