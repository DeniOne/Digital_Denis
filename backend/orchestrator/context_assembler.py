"""
Digital Den — Context Assembler (RAG 2.0)
═══════════════════════════════════════════════════════════════════════════

Структурированная сборка контекста для LLM с явными маркерами приоритетов.
"""

from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from memory.models import MemoryItem, ConversationState, UserSettings, Message


class ContextAssembler:
    """
    Собирает фреймированный контекст для LLM.
    
    Приоритет подачи (строгий порядок):
    1. System Rules (всегда в начале)
    2. Conversation State (если есть)
    3. Rules & Principles (из Long-Term Memory)
    4. Facts (High Confidence)
    5. Decisions
    6. Hypotheses (с маркером [UNCONFIRMED])
    7. Reflections / Failures
    8. Conflicts (если обнаружены)
    9. Last 3-5 messages (Short-Term)
    """
    
    async def assemble_context(
        self,
        user_message: str,
        user_settings: Optional[UserSettings],
        conversation_state: Optional[ConversationState],
        relevant_memories: List[Tuple[MemoryItem, float]],
        recent_messages: List[Dict],  # [{"role": "user|assistant", "content": "..."}]
        conflicts: List[Dict] = None,
    ) -> str:
        """
        Возвращает фреймированный контекст в виде текста.
        
        Args:
            user_message: Текущее сообщение пользователя
            user_settings: Настройки пользователя
            conversation_state: Состояние диалога
            relevant_memories: Список (MemoryItem, score) от RAG
            recent_messages: Последние сообщения
            conflicts: Обнаруженные конфликты
            
        Returns:
            str: Фреймированный контекст для LLM
        """
        sections = []
        
        # 0. Time context
        from datetime import datetime
        now = datetime.now()
        sections.append(f"[TIME CONTEXT]\nToday: {now.strftime('%Y-%m-%d')} ({now.strftime('%A')})\nCurrent Time: {now.strftime('%H:%M')}\n")

        # 1. System Rules
        if user_settings:
            sections.append(self._format_system_rules(user_settings))
        
        # 2. Conversation State
        if conversation_state:
            sections.append(self._format_conversation_state(conversation_state))
        
        # 3. Сортировка памяти по типам
        memories_by_type = self._group_by_type(relevant_memories)
        
        # 4. Rules & Principles
        rules_and_principles = memories_by_type.get("rule", []) + memories_by_type.get("principle", [])
        if rules_and_principles:
            sections.append(self._format_section(
                title="[RULES & PRINCIPLES]",
                note="Priority, no decay",
                memories=rules_and_principles
            ))
        
        # 5. Facts (High Confidence)
        high_confidence_facts = [
            (m, score) for m, score in memories_by_type.get("fact", [])
            if m.confidence_level == "high"
        ]
        if high_confidence_facts:
            sections.append(self._format_section(
                title="[FACTS — HIGH CONFIDENCE]",
                note="Verified",
                memories=high_confidence_facts
            ))
        
        # 6. Decisions
        if "decision" in memories_by_type:
            sections.append(self._format_section(
                title="[DECISIONS]",
                note="User-made",
                memories=memories_by_type["decision"]
            ))
        
        # 7. Hypotheses
        if "hypothesis" in memories_by_type:
            sections.append(self._format_section(
                title="[HYPOTHESES]",
                note="⚠️ NOT CONFIRMED",
                memories=memories_by_type["hypothesis"]
            ))
        
        # 8. Reflections / Failures
        reflections = memories_by_type.get("reflection", []) + memories_by_type.get("failure", [])
        if reflections:
            sections.append(self._format_section(
                title="[REFLECTIONS / FAILURES]",
                note="For analysis only",
                memories=reflections
            ))
        
        # 9. Insights
        if "insight" in memories_by_type:
            sections.append(self._format_section(
                title="[INSIGHTS]",
                note="Key observations",
                memories=memories_by_type["insight"]
            ))
        
        # 10. Conflicts
        if conflicts:
            sections.append(self._format_conflicts(conflicts))
        
        # 11. Recent messages
        if recent_messages:
            sections.append(self._format_recent_messages(recent_messages))
        
        # 12. Current message
        sections.append(f"\n[CURRENT USER MESSAGE]\n{user_message}\n")
        
        return "\n\n".join(sections)
    
    def _format_system_rules(self, settings: UserSettings) -> str:
        """Форматирует системные правила из UserSettings"""
        rules = ["[SYSTEM RULES]", ""]
        
        rules.append(f"AI Role: {settings.ai_role}")
        rules.append(f"Thinking Depth: {settings.thinking_depth}")
        rules.append(f"Response Style: {settings.response_style}")
        rules.append(f"Confrontation Level: {settings.confrontation_level}")
        rules.append(f"Initiative: {settings.initiative_level}")
        
        if settings.explain_mode != "off":
            rules.append(f"⚠️ Explain Mode: {settings.explain_mode} (показывать reasoning)")
        
        return "\n".join(rules)
    
    def _format_conversation_state(self, cs: ConversationState) -> str:
        """Форматирует Conversation State"""
        lines = ["[CONVERSATION STATE]", ""]
        
        if cs.topic:
            lines.append(f"📌 Topic: {cs.topic}")
        if cs.goal:
            lines.append(f"🎯 Goal: {cs.goal}")
        if cs.current_step:
            lines.append(f"📍 Current Step: {cs.current_step}")
        if cs.active_entities:
            lines.append(f"🔗 Active Entities: {', '.join(cs.active_entities)}")
        if cs.open_questions:
            lines.append(f"❓ Open Questions:")
            for q in cs.open_questions:
                lines.append(f"   - {q}")
        if cs.decisions_made:
            lines.append(f"✅ Decisions Made: {len(cs.decisions_made)}")
        
        return "\n".join(lines)
    
    def _format_section(
        self,
        title: str,
        note: str,
        memories: List[Tuple[MemoryItem, float]]
    ) -> str:
        """Форматирует секцию памяти"""
        if not memories:
            return ""
        
        lines = [title, f"({note})", ""]
        
        for mem, score in memories:
            # Confidence marker
            confidence_marker = {
                "high": "✓",
                "medium": "~",
                "low": "?",
                "unknown": "?"
            }.get(mem.confidence_level, "?")
            
            # Format line
            lines.append(f"{confidence_marker} [{mem.item_type}] {mem.content}")
            
            if mem.summary:
                lines.append(f"   Summary: {mem.summary}")
            
            # Метаданные (score, дата, usage)
            meta_parts = []
            if mem.created_at:
                meta_parts.append(f"Created: {mem.created_at.strftime('%Y-%m-%d')}")
            meta_parts.append(f"Score: {score:.2f}")
            if mem.usage_count > 0:
                meta_parts.append(f"Used: {mem.usage_count}x")
            
            lines.append(f"   ({', '.join(meta_parts)})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_conflicts(self, conflicts: List[Dict]) -> str:
        """Форматирует обнаруженные конфликты"""
        if not conflicts:
            return ""
        
        lines = ["[⚠️ CONFLICTS DETECTED]", ""]
        
        for conf in conflicts:
            lines.append(f"Type: {conf['type']} (confidence: {conf.get('confidence', 0.7):.1f})")
            lines.append(f"  A [{conf['memory_a'].item_type}]: {conf['memory_a'].content[:100]}...")
            lines.append(f"  B [{conf['memory_b'].item_type}]: {conf['memory_b'].content[:100]}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_recent_messages(self, messages: List[Dict]) -> str:
        """Форматирует последние сообщения"""
        if not messages:
            return ""
        
        lines = ["[RECENT CONVERSATION]", ""]
        
        for msg in messages[-5:]:  # последние 5
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            emoji = "👤" if role == "user" else "🤖"
            lines.append(f"{emoji} {role.upper()}: {content}")
        
        lines.append("")
        return "\n".join(lines)
    
    def _group_by_type(
        self,
        memories: List[Tuple[MemoryItem, float]]
    ) -> Dict[str, List[Tuple[MemoryItem, float]]]:
        """Группирует память по типам"""
        grouped = defaultdict(list)
        
        for mem, score in memories:
            grouped[mem.item_type].append((mem, score))
        
        return dict(grouped)


# Global instance
context_assembler = ContextAssembler()
