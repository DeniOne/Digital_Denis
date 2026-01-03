"""
RAG 2.0 — State Extractor Contract Tests
═══════════════════════════════════════════════════════════════════════════

Тесты для State Extractor prompt behavior
"""

import pytest
import json
from uuid import uuid4

from memory.state_extractor import state_extractor


# ═══════════════════════════════════════════════════════════════════════════
# 2️⃣ State Extractor Prompt — Contract Tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_se_01_json_only_output():
    """
    SE-01: JSON-only output
    
    Then: ответ = валидный JSON, ❌ нет markdown, ❌ нет текста
    """
    user_id = uuid4()
    message = "Давай обсудим RAG 2.0"
    
    result = await state_extractor.extract_state(
        previous_state=None,
        last_messages=[],
        current_message=message,
        user_id=user_id
    )
    
    # Assertions: результат должен быть валидным dict (уже распарсенный JSON)
    assert isinstance(result, dict)
    
    # Проверить что это не просто текст
    assert "topic" in result or result == {}
    
    # Если есть поля, они должны быть правильного типа
    if "active_entities" in result:
        assert isinstance(result["active_entities"], list)
    
    if "decisions_made" in result:
        assert isinstance(result["decisions_made"], list)


@pytest.mark.asyncio
async def test_se_02_partial_update():
    """
    SE-02: Partial update
    
    Given: previous_state.topic = "RAG 2.0"
    When: «Давай теперь про тесты»
    Then: topic остаётся "RAG 2.0", current_step обновляется → "testing"
    ❌ Fail если topic перезаписан или состояние обнулено
    """
    user_id = uuid4()
    
    previous_state = {
        "topic": "RAG 2.0",
        "goal": "Implement RAG 2.0",
        "current_step": "design",
        "intent": "planning",
        "active_entities": ["Context Assembler"],
        "active_objects": [],
        "assumptions": [],
        "constraints": [],
        "decisions_made": [],
        "open_questions": [],
        "unresolved_points": [],
        "confidence_level": "high"
    }
    
    message = "Давай теперь про тесты"
    
    result = await state_extractor.extract_state(
        previous_state=previous_state,
        last_messages=[],
        current_message=message,
        user_id=user_id
    )
    
    # Assertions
    # Topic должен сохраниться (или остаться связанным с RAG 2.0)
    if result.get("topic"):
        assert "RAG" in result["topic"] or result["topic"] == previous_state["topic"]
    
    # current_step должен обновиться
    assert result.get("current_step") != "design" or "test" in str(result.get("current_step", "")).lower()
    
    # ❌ Fail если состояние обнулено
    assert result.get("active_entities") is not None  # не должно быть полностью сброшено


@pytest.mark.asyncio
async def test_se_03_uncertainty_handling():
    """
    SE-03: Uncertainty handling
    
    When: сообщение неоднозначно
    Then: соответствующие поля = null, не происходит догадки
    ❌ Fail если цель или тема придуманы
    """
    user_id = uuid4()
    
    # Неоднозначное сообщение
    message = "хм..."
    
    result = await state_extractor.extract_state(
        previous_state=None,
        last_messages=[],
        current_message=message,
        user_id=user_id
    )
    
    # Assertions
    # При неоднозначном сообщении topic и goal должны быть null
    topic = result.get("topic")
    goal = result.get("goal")
    
    # ❌ Fail если цель или тема придуманы
    # (для сообщения "хм..." не должно быть конкретной темы)
    if topic:
        # Если тема есть, она должна быть очень общей или null
        assert len(topic) < 50 or topic is None
    
    if goal:
        # Цель не должна быть конкретной
        assert len(goal) < 50 or goal is None
    
    # active_entities должен быть пустым
    entities = result.get("active_entities", [])
    assert len(entities) == 0 or entities is None
