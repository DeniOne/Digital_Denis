"""
RAG 2.0 — Retrieval Logic Tests
═══════════════════════════════════════════════════════════════════════════

Тесты для intent-aware retrieval и time decay
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from memory.ranking_config import get_memory_weight, calculate_time_decay
from memory.rag2_search import rag2_search_service, detect_conflicts
from memory.models import MemoryItem


# ═══════════════════════════════════════════════════════════════════════════
# 3️⃣ RAG 2.0 Retrieval — Logic Tests
# ═══════════════════════════════════════════════════════════════════════════

def test_rag_ret_01_intent_aware_retrieval():
    """
    RAG-RET-01: Intent-aware retrieval
    
    Given: intent = decision_request
    Then: decision, principle, rule имеют приоритет, reflection/emotion понижены
    """
    intent = "decision_request"
    
    # Проверить веса для decision_request
    principle_weight = get_memory_weight("principle", intent)
    decision_weight = get_memory_weight("decision", intent)
    rule_weight = get_memory_weight("rule", intent)
    
    reflection_weight = get_memory_weight("reflection", intent)
    emotion_weight = get_memory_weight("emotion", intent)
    
    # Assertions
    assert principle_weight >= 1.2
    assert decision_weight >= 1.0
    assert rule_weight >= 1.2
    
    # ❌ Fail если эмоции/рефлексии имеют высокий приоритет
    assert reflection_weight <= 0.5
    assert emotion_weight <= 0.2
    
    # Принципы должны быть важнее эмоций
    assert principle_weight > emotion_weight * 5


def test_rag_ret_02_time_decay():
    """
    RAG-RET-02: Time decay
    
    Given: reflection (30 дней) vs reflection (1 день)
    Then: свежая reflection выше в ранжировании
    """
    now = datetime.utcnow()
    
    old_reflection_date = now - timedelta(days=30)
    fresh_reflection_date = now - timedelta(days=1)
    
    old_decay = calculate_time_decay("reflection", old_reflection_date, now)
    fresh_decay = calculate_time_decay("reflection", fresh_reflection_date, now)
    
    # Assertions
    assert fresh_decay > old_decay
    
    # ❌ Fail если время не влияет
    decay_difference = fresh_decay - old_decay
    assert decay_difference > 0.1  # значимая разница


def test_rag_ret_03_principle_immunity():
    """
    RAG-RET-03: Principle immunity
    
    Given: principle (2 года) vs hypothesis (вчера)
    Then: principle не теряет вес
    """
    now = datetime.utcnow()
    
    old_principle_date = now - timedelta(days=730)  # 2 года
    fresh_hypothesis_date = now - timedelta(days=1)
    
    principle_decay = calculate_time_decay("principle", old_principle_date, now)
    hypothesis_decay = calculate_time_decay("hypothesis", fresh_hypothesis_date, now)
    
    # Assertions
    # Принципы не деградируют
    assert principle_decay == 1.0
    
    # ❌ Fail если principle вытеснен гипотезой
    # Даже с учётом decay, principle должен быть конкурентоспособен
    principle_weight = get_memory_weight("principle", "decision_request")
    hypothesis_weight = get_memory_weight("hypothesis", "decision_request")
    
    principle_final = principle_weight * principle_decay
    hypothesis_final = hypothesis_weight * hypothesis_decay
    
    assert principle_final > hypothesis_final


def test_rag_ret_04_kaizen_boost():
    """
    RAG-RET-04: Kaizen boost
    
    Given: память с высокой эффективностью (positive_outcomes)
    Then: получает boost в ранжировании
    """
    # Создать мокап воспоминания с высокой эффективностью
    high_quality_memory = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="decision",
        content="Use RAG 2.0 architecture",
        usage_count=10,
        positive_outcomes=8,
        negative_outcomes=2,
        confidence_level="high",
        created_at=datetime.utcnow() - timedelta(days=7)
    )
    
    low_quality_memory = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="decision",
        content="Use simple approach",
        usage_count=10,
        positive_outcomes=3,
        negative_outcomes=7,
        confidence_level="medium",
        created_at=datetime.utcnow() - timedelta(days=7)
    )
    
    # Рассчитать Kaizen boost
    def calc_kaizen_boost(mem):
        total_outcomes = mem.positive_outcomes + mem.negative_outcomes
        if total_outcomes > 0:
            effectiveness = (mem.positive_outcomes - mem.negative_outcomes) / total_outcomes
            return 1.0 + (effectiveness * 0.15)
        return 1.0
    
    high_boost = calc_kaizen_boost(high_quality_memory)
    low_boost = calc_kaizen_boost(low_quality_memory)
    
    # Assertions
    assert high_boost > 1.0
    assert low_boost < 1.0
    assert high_boost > low_boost


def test_conflict_detection():
    """
    Test conflict detection between memories
    """
    decision1 = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="decision",
        content="Use PostgreSQL for database with vector support pgvector extension",
        created_at=datetime.utcnow()
    )
    
    hypothesis1 = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="hypothesis",
        content="Maybe we should use MongoDB for database with vector search capabilities",
        created_at=datetime.utcnow()
    )
    
    # Несвязанные воспоминания
    decision2 = MemoryItem(
        id=uuid4(),
        user_id=uuid4(),
        item_type="decision",
        content="Deploy on AWS infrastructure",
        created_at=datetime.utcnow()
    )
    
    memories = [decision1, hypothesis1, decision2]
    
    conflicts = detect_conflicts(memories)
    
    # Должен обнаружить конфликт между decision1 и hypothesis1
    assert len(conflicts) >= 1
    
    # Проверить что конфликт правильно идентифицирован
    conflict = conflicts[0]
    assert conflict["type"] == "decision_vs_hypothesis"
    assert conflict["memory_a"].item_type in ["decision", "hypothesis"]
    assert conflict["memory_b"].item_type in ["decision", "hypothesis"]
