"""
Digital Den — Settings API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for AI Control settings and Rules Engine.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from memory.models import UserSettings, User
from analytics.cal_models import Rule
from core.auth import get_current_user_optional


router = APIRouter(tags=["Settings"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

# --- Behavior ---
class BehaviorSettings(BaseModel):
    ai_role: str = Field(default="partner_strategic", description="AI role: partner_strategic, analyst_logical, coach_socratic, recorder_passive, explorer_hypothesis")
    thinking_depth: str = Field(default="structured", description="Thinking depth: shallow, structured, systemic, philosophical")
    response_style: str = Field(default="detailed", description="Response style: short, detailed")
    confrontation_level: str = Field(default="argumented", description="Confrontation level: none, soft, argumented, hard")


# --- Autonomy ---
class AutonomySettings(BaseModel):
    initiative_level: str = Field(default="suggest", description="Initiative: request_only, suggest, warn, proactive")
    intervention_frequency: str = Field(default="realtime", description="Frequency: realtime, post_session, daily_review, anomaly_detected")
    allowed_actions: List[str] = Field(default=["create_decisions", "link_memories"], description="Allowed actions")


# --- Memory ---
class MemorySettings(BaseModel):
    save_policy: str = Field(default="save_confirmed", description="Save policy: save_all, save_confirmed, save_marked")
    auto_archive_days: int = Field(default=365, ge=0, le=3650, description="Auto archive after N days (0 = disabled)")
    memory_trust_level: str = Field(default="cautious", description="Trust level: none, cautious, trusted")
    saved_types: List[str] = Field(default=["facts", "decisions", "hypotheses"], description="Types to save")


# --- Analytics ---
class AnalyticsSettings(BaseModel):
    analytics_types: List[str] = Field(default=["logical_contradictions", "recurring_topics"], description="Active analytics types")
    analytics_aggressiveness: str = Field(default="recommend", description="Aggressiveness: inform, recommend, warn, demand_attention")


# --- Kaizen Engine ---
class KaizenSettings(BaseModel):
    """Настройки Kaizen Engine."""
    adaptive_ai_enabled: bool = Field(default=True, description="Включить адаптивное поведение ИИ")
    show_mirror: bool = Field(default=True, description="Показывать Kaizen-зеркало")
    comparison_period: str = Field(
        default="month",
        description="Период сравнения: week, month, quarter, half_year, year, all_time"
    )
    
    # Маппинг периодов на дни
    @property
    def comparison_days(self) -> Optional[int]:
        mapping = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "half_year": 180,
            "year": 365,
            "all_time": None,
        }
        return mapping.get(self.comparison_period, 30)


# --- Full Settings ---
class UserSettingsSchema(BaseModel):
    behavior: BehaviorSettings = Field(default_factory=BehaviorSettings)
    autonomy: AutonomySettings = Field(default_factory=AutonomySettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    kaizen: KaizenSettings = Field(default_factory=KaizenSettings)
    
    class Config:
        from_attributes = True


class UserSettingsResponse(UserSettingsSchema):
    id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Rules ---
class RuleCreate(BaseModel):
    scope: str = Field(default="global", description="Scope: global, context")
    trigger: str = Field(default="always", description="Trigger: always, topic, mode, session")
    instruction: str = Field(..., min_length=1, max_length=2000, description="Rule instruction (free text)")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    context_topic_id: Optional[str] = None
    context_mode: Optional[str] = None


class RuleUpdate(BaseModel):
    instruction: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    context_topic_id: Optional[str] = None
    context_mode: Optional[str] = None
    sort_order: Optional[int] = None


class RuleResponse(BaseModel):
    id: str
    scope: str
    trigger: str
    instruction: str
    priority: str
    is_active: bool
    context_topic_id: Optional[str] = None
    context_mode: Optional[str] = None
    sort_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

async def get_or_create_settings(db: AsyncSession, user_id: UUID) -> UserSettings:
    """Get user settings or create default ones."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


def settings_to_response(settings: UserSettings) -> dict:
    """Convert UserSettings model to response dict."""
    return {
        "id": str(settings.id),
        "user_id": str(settings.user_id),
        "behavior": {
            "ai_role": settings.ai_role,
            "thinking_depth": settings.thinking_depth,
            "response_style": settings.response_style,
            "confrontation_level": settings.confrontation_level,
        },
        "autonomy": {
            "initiative_level": settings.initiative_level,
            "intervention_frequency": settings.intervention_frequency,
            "allowed_actions": settings.allowed_actions or [],
        },
        "memory": {
            "save_policy": settings.save_policy,
            "auto_archive_days": settings.auto_archive_days,
            "memory_trust_level": settings.memory_trust_level,
            "saved_types": settings.saved_types or [],
        },
        "analytics": {
            "analytics_types": settings.analytics_types or [],
            "analytics_aggressiveness": settings.analytics_aggressiveness,
        },
        "created_at": settings.created_at.isoformat() if settings.created_at else None,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


def rule_to_response(rule: Rule) -> dict:
    """Convert Rule model to response dict."""
    return {
        "id": str(rule.id),
        "scope": rule.scope,
        "trigger": rule.trigger,
        "instruction": rule.instruction,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "context_topic_id": str(rule.context_topic_id) if rule.context_topic_id else None,
        "context_mode": rule.context_mode,
        "sort_order": rule.sort_order or 0,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Settings Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    telegram_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get all user settings."""
    user_id = current_user.id if current_user else None
    
    # Resolve telegram_id
    if telegram_id:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user_id = user.id
            
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    settings = await get_or_create_settings(db, user_id)
    return settings_to_response(settings)


@router.put("")
async def update_settings(
    data: UserSettingsSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update all user settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    # Update behavior
    settings.ai_role = data.behavior.ai_role
    settings.thinking_depth = data.behavior.thinking_depth
    settings.response_style = data.behavior.response_style
    settings.confrontation_level = data.behavior.confrontation_level
    
    # Update autonomy
    settings.initiative_level = data.autonomy.initiative_level
    settings.intervention_frequency = data.autonomy.intervention_frequency
    settings.allowed_actions = data.autonomy.allowed_actions
    
    # Update memory
    settings.save_policy = data.memory.save_policy
    settings.auto_archive_days = data.memory.auto_archive_days
    settings.memory_trust_level = data.memory.memory_trust_level
    settings.saved_types = data.memory.saved_types
    
    # Update analytics
    settings.analytics_types = data.analytics.analytics_types
    settings.analytics_aggressiveness = data.analytics.analytics_aggressiveness
    
    await db.commit()
    await db.refresh(settings)
    
    return settings_to_response(settings)


@router.patch("/behavior")
async def update_behavior_settings(
    data: BehaviorSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update only behavior settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    settings.ai_role = data.ai_role
    settings.thinking_depth = data.thinking_depth
    settings.response_style = data.response_style
    settings.confrontation_level = data.confrontation_level
    
    await db.commit()
    await db.refresh(settings)
    
    return {"status": "updated", "behavior": data.model_dump()}


@router.patch("/autonomy")
async def update_autonomy_settings(
    data: AutonomySettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update only autonomy settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    settings.initiative_level = data.initiative_level
    settings.intervention_frequency = data.intervention_frequency
    settings.allowed_actions = data.allowed_actions
    
    await db.commit()
    await db.refresh(settings)
    
    return {"status": "updated", "autonomy": data.model_dump()}


@router.patch("/memory")
async def update_memory_settings(
    data: MemorySettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update only memory settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    settings.save_policy = data.save_policy
    settings.auto_archive_days = data.auto_archive_days
    settings.memory_trust_level = data.memory_trust_level
    settings.saved_types = data.saved_types
    
    await db.commit()
    await db.refresh(settings)
    
    return {"status": "updated", "memory": data.model_dump()}


@router.patch("/analytics")
async def update_analytics_settings(
    data: AnalyticsSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update only analytics settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    settings.analytics_types = data.analytics_types
    settings.analytics_aggressiveness = data.analytics_aggressiveness
    
    await db.commit()
    await db.refresh(settings)
    
    return {"status": "updated", "analytics": data.model_dump()}


@router.get("/kaizen")
async def get_kaizen_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get Kaizen Engine settings."""
    settings = await get_or_create_settings(db, current_user.id)
    
    return {
        "adaptive_ai_enabled": getattr(settings, 'kaizen_adaptive_ai_enabled', True),
        "show_mirror": getattr(settings, 'kaizen_show_mirror', True),
        "comparison_period": getattr(settings, 'kaizen_comparison_period', 'month'),
        "period_options": [
            {"value": "week", "label": "Неделя", "days": 7},
            {"value": "month", "label": "Месяц", "days": 30},
            {"value": "quarter", "label": "Квартал", "days": 90},
            {"value": "half_year", "label": "Полгода", "days": 180},
            {"value": "year", "label": "Год", "days": 365},
            {"value": "all_time", "label": "Всё время", "days": None},
        ],
    }


@router.patch("/kaizen")
async def update_kaizen_settings(
    data: KaizenSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update Kaizen Engine settings."""
    valid_periods = ["week", "month", "quarter", "half_year", "year", "all_time"]
    if data.comparison_period not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period. Choose: {', '.join(valid_periods)}"
        )
    
    settings = await get_or_create_settings(db, current_user.id)
    
    settings.kaizen_adaptive_ai_enabled = data.adaptive_ai_enabled
    settings.kaizen_show_mirror = data.show_mirror
    settings.kaizen_comparison_period = data.comparison_period
    
    await db.commit()
    await db.refresh(settings)
    
    return {
        "status": "updated",
        "kaizen": {
            "adaptive_ai_enabled": data.adaptive_ai_enabled,
            "show_mirror": data.show_mirror,
            "comparison_period": data.comparison_period,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# Rules Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    scope: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get all rules for user."""
    query = select(Rule).where(Rule.user_id == current_user.id)
    
    if scope:
        query = query.where(Rule.scope == scope)
    
    query = query.order_by(Rule.sort_order, Rule.created_at)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [rule_to_response(r) for r in rules]


@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Create a new rule."""
    rule = Rule(
        user_id=current_user.id,
        scope=data.scope,
        trigger=data.trigger,
        instruction=data.instruction,
        priority=data.priority,
        context_topic_id=UUID(data.context_topic_id) if data.context_topic_id else None,
        context_mode=data.context_mode,
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return rule_to_response(rule)


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get a specific rule."""
    result = await db.execute(
        select(Rule).where(
            Rule.id == UUID(rule_id),
            Rule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule_to_response(rule)


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update a rule."""
    result = await db.execute(
        select(Rule).where(
            Rule.id == UUID(rule_id),
            Rule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Update only provided fields
    if data.instruction is not None:
        rule.instruction = data.instruction
    if data.priority is not None:
        rule.priority = data.priority
    if data.is_active is not None:
        rule.is_active = data.is_active
    if data.context_topic_id is not None:
        rule.context_topic_id = UUID(data.context_topic_id) if data.context_topic_id else None
    if data.context_mode is not None:
        rule.context_mode = data.context_mode
    if data.sort_order is not None:
        rule.sort_order = data.sort_order
    
    await db.commit()
    await db.refresh(rule)
    
    return rule_to_response(rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Delete a rule."""
    result = await db.execute(
        select(Rule).where(
            Rule.id == UUID(rule_id),
            Rule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    return {"status": "deleted", "id": rule_id}


@router.patch("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Toggle rule active status."""
    result = await db.execute(
        select(Rule).where(
            Rule.id == UUID(rule_id),
            Rule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = not rule.is_active
    await db.commit()
    
    return {"status": "toggled", "id": rule_id, "is_active": rule.is_active}


# ═══════════════════════════════════════════════════════════════════════════
# Explain Mode Endpoints
# ═══════════════════════════════════════════════════════════════════════════

class ExplainModeUpdate(BaseModel):
    mode: str = Field(..., description="Explain mode: off, brief, detailed")


@router.get("/explain-mode")
async def get_explain_mode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get current explain mode setting."""
    settings = await get_or_create_settings(db, current_user.id)
    return {
        "explain_mode": getattr(settings, 'explain_mode', 'off') or 'off',
        "options": ["off", "brief", "detailed"],
        "descriptions": {
            "off": "Режим объяснения выключен",
            "brief": "Краткое объяснение логики (1-2 предложения)",
            "detailed": "Подробное объяснение с альтернативами",
        }
    }


@router.patch("/explain-mode")
async def update_explain_mode(
    data: ExplainModeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Update explain mode setting."""
    if data.mode not in ["off", "brief", "detailed"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Choose: off, brief, detailed")
    
    settings = await get_or_create_settings(db, current_user.id)
    settings.explain_mode = data.mode
    await db.commit()
    
    return {
        "status": "updated",
        "explain_mode": data.mode,
        "message": {
            "off": "Режим объяснения выключен",
            "brief": "Включён краткий режим объяснения",
            "detailed": "Включён подробный режим объяснения",
        }.get(data.mode)
    }


@router.post("/explain-mode/toggle")
async def toggle_explain_mode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Cycle through explain modes: off -> brief -> detailed -> off."""
    settings = await get_or_create_settings(db, current_user.id)
    
    current = getattr(settings, 'explain_mode', 'off') or 'off'
    cycle = {"off": "brief", "brief": "detailed", "detailed": "off"}
    new_mode = cycle.get(current, "off")
    
    settings.explain_mode = new_mode
    await db.commit()
    
    return {
        "status": "toggled",
        "previous": current,
        "explain_mode": new_mode,
        "message": {
            "off": "🔕 Режим объяснения выключен",
            "brief": "💡 Включён краткий режим объяснения",
            "detailed": "🧠 Включён подробный режим объяснения",
        }.get(new_mode)
    }

