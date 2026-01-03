"""
RAG 2.0 — Context Assembler Tests
═══════════════════════════════════════════════════════════════════════════

Тесты для Context Assembler (priority order, conflict surfacing)
"""

import pytest
from uuid import uuid4
from datetime import datetime

from orchestrator.context_assembler import context_assembler
from memory.models import MemoryItem, ConversationState


# ═══════════════════════════════════════════════════════════════════════════
# 4️⃣ Context Assembler — Integration Tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ca_01_priority_order():
    """
    CA-01: Priority order
    
    Контекст должен быть строго:
    1. System Rules
    2. Conversation State
    3. Rules / Principles
    4. Facts
    5. Decisions
    6. Last messages
    
    ❌ Fail если CS ниже истории сообщений
    """
    # Создать мокапы
    user_message = "What should I do?"
    
    conversation_state = ConversationState(
        id=uuid4(),
        user_id=uuid4(),
        conversation_id="test_chat",
        topic="RAG 2.0",
        goal="Implement RAG 2.0",
        current_step="testing",
        intent="decision_request",
        active_entities=["Context Assembler"],
        confidence_level="high"
    )
    
    relevant_memories = [
        (MemoryItem(
            id=uuid4(),
            user_id=uuid4(),
            item_type="principle",
            content="Always prioritize user clarity",
            confidence_level="high",
            created_at=datetime.utcnow()
        ), 0.95),
        (MemoryItem(
            id=uuid4(),
            user_id=uuid4(),
            item_type="fact",
            content="RAG 2.0 uses intent-aware retrieval",
            confidence_level="high",
            created_at=datetime.utcnow()
        ), 0.90),
        (MemoryItem(
            id=uuid4(),
            user_id=uuid4(),
            item_type="decision",
            content="Use PostgreSQL for storage",
            confidence_level="medium",
            created_at=datetime.utcnow()
        ), 0.85),
    ]
    
    recent_messages = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуй!"},
    ]
    
    # Собрать контекст
    framed_context = await context_assembler.assemble_context(
        user_message=user_message,
        user_settings=None,
        conversation_state=conversation_state,
        relevant_memories=relevant_memories,
        recent_messages=recent_messages,
        conflicts=None
    )
    
    # Assertions: проверить порядок секций
    lines = framed_context.split("\n")
    
    # Найти индексы ключевых секций
    cs_index = None
    principles_index = None
    facts_index = None
    recent_index = None
    
    for idx, line in enumerate(lines):
        if "[CONVERSATION STATE]" in line:
            cs_index = idx
        elif "[RULES & PRINCIPLES]" in line:
            principles_index = idx
        elif "[FACTS" in line:
            facts_index = idx
        elif "[RECENT CONVERSATION]" in line:
            recent_index = idx
    
    # CS должен быть ВЫШЕ истории сообщений
    if cs_index and recent_index:
        assert cs_index < recent_index, "❌ FAIL: CS ниже истории сообщений"
    
    # Principles должны быть выше Facts
    if principles_index and facts_index:
        assert principles_index < facts_index
    
    # Facts должны быть выше Recent messages
    if facts_index and recent_index:
        assert facts_index < recent_index


@pytest.mark.asyncio
async def test_ca_02_conflict_surfacing():
    """
    CA-02: Conflict surfacing
    
    Given: два решения противоречат
    Then: в контексте появляется блок [CONFLICTS]
    ❌ Fail если конфликт замалчивается
    """
    user_message = "Which database should we use?"
    
    relevant_memories = [
        (MemoryItem(
            id=uuid4(),
            user_id=uuid4(),
            item_type="decision",
            content="Use PostgreSQL with pgvector",
            confidence_level="high",
            created_at=datetime.utcnow()
        ), 0.95),
    ]
    
    # Конфликт
    conflicts = [
        {
            "memory_a": MemoryItem(
                id=uuid4(),
                user_id=uuid4(),
                item_type="decision",
                content="Use PostgreSQL with pgvector",
                confidence_level="high",
                created_at=datetime.utcnow()
            ),
            "memory_b": MemoryItem(
                id=uuid4(),
                user_id=uuid4(),
                item_type="hypothesis",
                content="Maybe we should use MongoDB with vector search",
                confidence_level="medium",
                created_at=datetime.utcnow()
            ),
            "type": "decision_vs_hypothesis",
            "confidence": 0.8
        }
    ]
    
    framed_context = await context_assembler.assemble_context(
        user_message=user_message,
        user_settings=None,
        conversation_state=None,
        relevant_memories=relevant_memories,
        recent_messages=[],
        conflicts=conflicts
    )
    
    # Assertions
    assert "[⚠️ CONFLICTS DETECTED]" in framed_context or "[CONFLICTS]" in framed_context
    
    # ❌ Fail если конфликт замалчивается
    assert "PostgreSQL" in framed_context
    assert "MongoDB" in framed_context or "decision_vs_hypothesis" in framed_context


@pytest.mark.asyncio
async def test_ca_03_confidence_markers():
    """
    CA-03: Confidence markers
    
    Then: каждое воспоминание должно иметь маркер уверенности (✓, ~, ?)
    """
    high_confidence_memory = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="fact",
        content="RAG 2.0 is implemented",
        confidence_level="high",
        created_at=datetime.utcnow()
    )
    
    medium_confidence_memory = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="hypothesis",
        content="This might work",
        confidence_level="medium",
        created_at=datetime.utcnow()
    )
    
    low_confidence_memory = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="thought",
        content="Just an idea",
        confidence_level="low",
        created_at=datetime.utcnow()
    )
    
    relevant_memories = [
        (high_confidence_memory, 0.9),
        (medium_confidence_memory, 0.7),
        (low_confidence_memory, 0.5),
    ]
    
    framed_context = await context_assembler.assemble_context(
        user_message="Test",
        user_settings=None,
        conversation_state=None,
        relevant_memories=relevant_memories,
        recent_messages=[],
        conflicts=None
    )
    
    # Assertions: должны присутствовать маркеры
    assert "✓" in framed_context  # high confidence
    assert "~" in framed_context or "?" in framed_context  # medium/low confidence
