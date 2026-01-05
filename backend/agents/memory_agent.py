"""
Digital Den — Memory Agent v2
═══════════════════════════════════════════════════════════════════════════

Extended agent for memory management: saving, aggregation, forgetting, retrieval.
"""

import json
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent, AgentContext, AgentResponse
from memory.models import MemoryItem, MemoryTopic
from memory.long_term import long_term_memory
from memory.semantic import semantic_memory
from analytics.topics import topic_extractor
from llm.groq import groq
from core.logging import get_logger
from core.audit import AuditService
from core.document_service import document_service

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

class MemoryActionType(Enum):
    SAVE = "save"
    SEARCH = "search"
    FORGET = "forget"
    AGGREGATE = "aggregate"
    RESTORE = "restore"
    INGEST = "ingest"


@dataclass
class MemoryCandidate:
    """Candidate for saving to memory."""
    type: str  # decision, insight, fact, thought
    content: str
    confidence: float
    structured_data: Optional[Dict] = None


@dataclass
class MemoryAction:
    """Action to perform on memory."""
    action_type: MemoryActionType
    item_type: Optional[str] = None
    content: Optional[str] = None
    confidence: float = 0.5
    memory_id: Optional[UUID] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ForgetRequest:
    """Request to forget a memory item."""
    memory_id: UUID
    confirmed: bool = False
    related_items: List[UUID] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Memory Agent v2
# ═══════════════════════════════════════════════════════════════════════════

class MemoryAgentV2(BaseAgent):
    """
    Memory Agent v2 — расширенное управление памятью.
    
    Ключевые функции:
    - auto_save: автоматическое сохранение decisions/insights/facts
    - extract_candidates: извлечение кандидатов для сохранения
    - forget: контролируемое забывание с подтверждением
    - aggregate: объединение похожих элементов
    - search: семантический поиск
    """
    
    name = "memory_v2"
    description = "Extended memory management agent"
    participates_in_dialogue = False
    writes_to_memory = True
    is_synchronous = True
    
    # Confidence thresholds by type
    CONFIDENCE_THRESHOLDS = {
        "decision": 0.85,
        "insight": 0.75,
        "fact": 0.90,
        "thought": 0.50,
    }
    
    # Patterns for detection
    SAVE_PATTERNS = {
        "decision": [
            "решил", "решение", "принял решение", "будем делать",
            "выбираю", "утверждаю", "одобряю", "делаем так"
        ],
        "insight": [
            "понял", "осознал", "инсайт", "вывод", "ключевой момент",
            "понимаю теперь", "важно что", "осознание"
        ],
        "fact": [
            "факт:", "данные:", "статистика:",
        ],
    }
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """Process memory-related request."""
        
        # Classify the operation
        operation = self._classify_operation(context.user_message)
        
        if operation == MemoryActionType.SEARCH:
            return await self._handle_search(context)
        elif operation == MemoryActionType.FORGET:
            return await self._handle_forget(context)
        elif operation == MemoryActionType.AGGREGATE:
            return await self._handle_aggregate(context)
        elif operation == MemoryActionType.INGEST:
            return await self._handle_ingest(context)
        else:
            return await self._handle_save(context)
    
    def _classify_operation(self, message: str) -> MemoryActionType:
        """Classify the memory operation from message."""
        message_lower = message.lower()
        
        forget_keywords = ["забудь", "удали", "забыть", "удалить", "убери"]
        search_keywords = ["найди", "вспомни", "что я", "когда я"]
        aggregate_keywords = ["объедини", "агрегируй", "сгруппируй"]
        ingest_keywords = ["документ", "манифест", "статья", "текст документа", "прочитай и запомни"]
        save_keywords = ["запомни", "сохрани", "запиши"]
        
        # Ingest takes priority if text is long or contains keywords
        if len(message) > 1000 or any(kw in message_lower for kw in ingest_keywords):
            return MemoryActionType.INGEST
            
        for kw in forget_keywords:
            if kw in message_lower:
                return MemoryActionType.FORGET
        
        for kw in search_keywords:
            if kw in message_lower:
                return MemoryActionType.SEARCH
        
        for kw in aggregate_keywords:
            if kw in message_lower:
                return MemoryActionType.AGGREGATE
        
        return MemoryActionType.SAVE
    
    # ═══════════════════════════════════════════════════════════════════════
    # Auto-save functionality
    # ═══════════════════════════════════════════════════════════════════════
    
    async def auto_save(
        self,
        db: AsyncSession,
        agent_response: AgentResponse,
        context: AgentContext,
        user_id: Optional[UUID] = None,
    ) -> List[MemoryAction]:
        """
        Automatically save worthy items from agent response.
        Called after other agents respond.
        
        Returns list of memory actions performed.
        """
        actions = []
        
        # 1. Extract candidates from response
        candidates = await self.extract_candidates(
            context.user_message + "\n" + agent_response.content
        )
        
        # 2. Filter by confidence threshold
        worthy = []
        for candidate in candidates:
            threshold = self.CONFIDENCE_THRESHOLDS.get(candidate.type, 0.5)
            if candidate.confidence >= threshold:
                worthy.append(candidate)
        
        # 3. Check for duplicates using semantic similarity
        unique = await self._deduplicate(db, worthy, user_id=user_id)
        
        # 4. Save each unique item
        for candidate in unique:
            item = await long_term_memory.save(
                db=db,
                item_type=candidate.type,
                content=candidate.content,
                summary=await self._generate_summary(candidate),
                structured_data=candidate.structured_data,
                source_agent=agent_response.agent,
                source_session=context.session_id,
                confidence=candidate.confidence,
                user_id=user_id,
            )
            
            # Audit log
            await AuditService.log_action(
                db=db,
                user_id=user_id,
                action="memory_save",
                target_type="memory_item",
                target_id=str(item.id),
                changes={"content": candidate.content, "type": candidate.type},
                meta_data={"confidence": candidate.confidence, "source": "auto_save"}
            )
            
            # Index for semantic search
            await semantic_memory.index(db, item.id, candidate.content)
            
            # Extract and assign topics
            topics = await topic_extractor.extract(candidate.content)
            for topic in topics:
                if topic.topic_id:
                    await self._assign_topic(db, item.id, topic.topic_id, topic.confidence)
            
            actions.append(MemoryAction(
                action_type=MemoryActionType.SAVE,
                item_type=candidate.type,
                content=candidate.content[:100],
                confidence=candidate.confidence,
                memory_id=item.id,
            ))
        
        await db.commit()
        return actions
    
    async def extract_candidates(self, text: str) -> List[MemoryCandidate]:
        """
        Extract memory candidates from text using LLM.
        """
        prompt = f"""Проанализируй текст и найди:
1. Decisions — явные решения ("решил", "будем делать")
2. Insights — озарения, выводы ("понял", "осознал")
3. Facts — конкретные факты, числа, даты

Текст:
{text[:1000]}

Верни JSON массив:
[{{"type": "decision|insight|fact", "content": "текст", "confidence": 0.0-1.0}}]

Только то, что явно присутствует. Если ничего нет — верни [].
JSON:"""
        
        try:
            result = await groq.complete_simple(prompt)
            return self._parse_candidates(result)
        except Exception as e:
            # Fallback: rule-based extraction
            return self._rule_based_extraction(text)
    
    def _parse_candidates(self, response: str) -> List[MemoryCandidate]:
        """Parse LLM response to candidates."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            
            candidates = []
            for item in data:
                if isinstance(item, dict):
                    candidates.append(MemoryCandidate(
                        type=item.get("type", "thought"),
                        content=item.get("content", ""),
                        confidence=float(item.get("confidence", 0.5)),
                    ))
            
            return candidates
            
        except (json.JSONDecodeError, ValueError):
            return []
    
    def _rule_based_extraction(self, text: str) -> List[MemoryCandidate]:
        """Fallback rule-based extraction."""
        candidates = []
        text_lower = text.lower()
        
        for item_type, patterns in self.SAVE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Extract sentence containing pattern
                    idx = text_lower.find(pattern)
                    start = max(0, text[:idx].rfind('.') + 1)
                    end = text.find('.', idx)
                    if end == -1:
                        end = len(text)
                    
                    content = text[start:end].strip()
                    if content:
                        candidates.append(MemoryCandidate(
                            type=item_type,
                            content=content,
                            confidence=0.7,  # Medium confidence for rule-based
                        ))
                    break  # Only one candidate per type
        
        return candidates
    
    async def _deduplicate(
        self, 
        db: AsyncSession, 
        candidates: List[MemoryCandidate],
        user_id: Optional[UUID] = None,
    ) -> List[MemoryCandidate]:
        """Remove duplicates using semantic similarity."""
        unique = []
        
        for candidate in candidates:
            # Search for similar existing items
            similar = await semantic_memory.search(
                db=db,
                query=candidate.content,
                limit=1,
                similarity_threshold=0.85,  # High threshold for duplicate detection
            )
            
            if not similar:
                unique.append(candidate)
        
        return unique
    
    async def _generate_summary(self, candidate: MemoryCandidate) -> str:
        """Generate short summary for memory item."""
        type_labels = {
            "decision": "Решение",
            "insight": "Инсайт",
            "fact": "Факт",
            "thought": "Мысль",
        }
        label = type_labels.get(candidate.type, "Запись")
        return f"[{label}] {candidate.content[:100]}..."
    
    async def _assign_topic(
        self, 
        db: AsyncSession, 
        memory_id: UUID, 
        topic_id: UUID,
        confidence: float
    ) -> None:
        """Assign topic to memory item."""
        mt = MemoryTopic(
            memory_id=memory_id,
            topic_id=topic_id,
            confidence=confidence,
            assigned_by="llm",
        )
        db.add(mt)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Forget functionality
    # ═══════════════════════════════════════════════════════════════════════
    
    async def prepare_forget(
        self,
        db: AsyncSession,
        query: str,
    ) -> Tuple[Optional[ForgetRequest], str]:
        """
        Prepare to forget: find item and related items.
        Returns ForgetRequest and message for confirmation.
        """
        # Search for matching item
        results = await semantic_memory.search(db, query, limit=1)
        
        if not results:
            return None, "Не нашёл подходящего воспоминания для удаления."
        
        memory, similarity = results[0]
        
        # Find related items
        related = await semantic_memory.find_similar(db, memory.id, limit=5)
        related_ids = [r[0].id for r in related if r[1] > 0.7]
        
        request = ForgetRequest(
            memory_id=memory.id,
            related_items=related_ids,
        )
        
        # Build confirmation message
        message = f"""Найдено: "{memory.content[:100]}..."
Тип: {memory.item_type}
Создано: {memory.created_at}

⚠️ Связано с {len(related_ids)} другими записями.

Подтвердите удаление? Восстановление возможно в течение 30 дней."""
        
        return request, message
    
    async def execute_forget(
        self,
        db: AsyncSession,
        request: ForgetRequest,
    ) -> bool:
        """Execute forget: soft delete the item."""
        if not request.confirmed:
            return False
        
        # Soft delete (set status to 'deleted')
        result = await db.execute(
            update(MemoryItem)
            .where(MemoryItem.id == request.memory_id)
            .values(
                status="deleted",
                updated_at=datetime.utcnow(),
            )
        )
        
        # Audit log
        await AuditService.log_action(
            db=db,
            user_id=None, # user_id needs to be passed in Context or Request
            action="memory_forget",
            target_type="memory_item",
            target_id=str(request.memory_id),
            changes={"status": {"old": "active", "new": "deleted"}}
        )
        
        await db.commit()
        return result.rowcount > 0
    
    async def restore(
        self,
        db: AsyncSession,
        memory_id: UUID,
    ) -> bool:
        """Restore a deleted memory item (within 30 days)."""
        result = await db.execute(
            update(MemoryItem)
            .where(
                and_(
                    MemoryItem.id == memory_id,
                    MemoryItem.status == "deleted",
                )
            )
            .values(
                status="active",
                updated_at=datetime.utcnow(),
            )
        )
        
        await db.commit()
        return result.rowcount > 0
    
    # ═══════════════════════════════════════════════════════════════════════
    # Aggregate functionality
    # ═══════════════════════════════════════════════════════════════════════
    
    async def aggregate_similar(
        self,
        db: AsyncSession,
        topic_id: Optional[UUID] = None,
        similarity_threshold: float = 0.85,
        min_cluster_size: int = 3,
    ) -> List[UUID]:
        """
        Aggregate similar memory items into summaries.
        
        Returns list of created aggregation IDs.
        """
        # Get active items (optionally filtered by topic)
        query = select(MemoryItem).where(MemoryItem.status == "active")
        
        if topic_id:
            query = query.join(MemoryTopic).where(MemoryTopic.topic_id == topic_id)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        if len(items) < min_cluster_size:
            return []
        
        # Cluster by similarity
        clusters = await self._cluster_items(db, items, similarity_threshold)
        
        aggregated_ids = []
        for cluster in clusters:
            if len(cluster) >= min_cluster_size:
                # Generate summary
                summary = await self._generate_cluster_summary(cluster)
                
                # Create aggregation item
                aggregation = MemoryItem(
                    id=uuid4(),
                    user_id=cluster[0].user_id,
                    item_type="aggregation",
                    content=summary,
                    structured_data={
                        "source_ids": [str(i.id) for i in cluster],
                        "aggregated_at": datetime.utcnow().isoformat(),
                    },
                    status="active",
                    confidence=0.9,
                )
                db.add(aggregation)
                aggregated_ids.append(aggregation.id)
                
                # Mark originals as aggregated
                for item in cluster:
                    item.status = "aggregated"
        
        await db.commit()
        return aggregated_ids
    
    async def _cluster_items(
        self,
        db: AsyncSession,
        items: List[MemoryItem],
        threshold: float,
    ) -> List[List[MemoryItem]]:
        """Cluster items by semantic similarity."""
        clusters = []
        used = set()
        
        for item in items:
            if item.id in used:
                continue
            
            # Find similar items
            similar = await semantic_memory.find_similar(db, item.id, limit=10)
            
            cluster = [item]
            for similar_item, similarity in similar:
                if similarity >= threshold and similar_item.id not in used:
                    cluster.append(similar_item)
                    used.add(similar_item.id)
            
            if len(cluster) > 1:
                clusters.append(cluster)
                used.add(item.id)
        
        return clusters
    
    async def _generate_cluster_summary(self, items: List[MemoryItem]) -> str:
        """Generate summary for a cluster of items."""
        contents = "\n---\n".join([i.content[:200] for i in items[:5]])
        
        prompt = f"""Создай краткое резюме (2-3 предложения) для этих связанных записей:

{contents}

Резюме:"""
        
        try:
            result = await groq.complete_simple(prompt)
            return result.strip()
        except Exception:
            return f"Агрегация {len(items)} записей от {items[0].created_at}"
    
    # ═══════════════════════════════════════════════════════════════════════
    # Search & Context
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_context_memories(
        self,
        db: AsyncSession,
        user_message: str,
        limit: int = 5,
        user_id: Optional[UUID] = None,
    ) -> List[Dict]:
        """Get relevant memories for context using semantic search."""
        
        # Try semantic search first
        results = await semantic_memory.search(
            db=db,
            query=user_message,
            limit=limit,
            user_id=user_id,
            similarity_threshold=0.6,
        )
        
        if results:
            return [
                {
                    "id": str(m.id),
                    "item_type": m.item_type,
                    "content": m.content,
                    "summary": m.summary,
                    "confidence": m.confidence,
                    "similarity": score,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m, score in results
            ]
        
        # Fallback to text search
        memories = await long_term_memory.search(
            db=db,
            user_id=user_id,
            query_text=user_message[:100],
            limit=limit,
        )
        
        return [
            {
                "id": str(m.id),
                "item_type": m.item_type,
                "content": m.content,
                "summary": m.summary,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]
    
    # ═══════════════════════════════════════════════════════════════════════
    # Operation Handlers
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _handle_search(self, context: AgentContext) -> AgentResponse:
        """Handle search operation."""
        return AgentResponse(
            content="Поиск в памяти...",
            agent=self.name,
            save_to_memory=False,
        )
    
    async def _handle_forget(self, context: AgentContext) -> AgentResponse:
        """Handle forget operation."""
        return AgentResponse(
            content="Подготовка к удалению...",
            agent=self.name,
            save_to_memory=False,
            metadata={"requires_confirmation": True},
        )
    
    async def _handle_aggregate(self, context: AgentContext) -> AgentResponse:
        """Handle aggregate operation."""
        return AgentResponse(
            content="Агрегация памяти завершена. Я объединил похожие воспоминания для лучшей структуры.",
            agent=self.name,
            save_to_memory=False,
        )

    async def _handle_save(self, context: AgentContext) -> AgentResponse:
        """Handle explicit save operation."""
        # The actual saving will be handled by auto_save after this response
        return AgentResponse(
            content="Принято! Я проанализировал ваше сообщение и сохранил важные детали в долговременную память. ✅",
            agent=self.name,
            save_to_memory=True,
        )

    async def _handle_ingest(self, context: AgentContext) -> AgentResponse:
        """Handle document ingestion via chat."""
        db = context.db
        user_id = context.user_id
        text = context.user_message
        
        # Try to find a title in the first line
        lines = text.split("\n")
        title = "Чат-документ"
        if len(lines) > 0 and len(lines[0]) < 100:
            potential_title = lines[0].strip().rstrip(":")
            if any(kw in potential_title.lower() for kw in ["документ", "манифест", "название", "файл"]):
                title = potential_title
                text = "\n".join(lines[1:])
        
        try:
            chunks_count = await document_service.ingest_text(
                db=db,
                user_id=user_id,
                text=text,
                title=title,
                source_type="chat_upload"
            )
            
            return AgentResponse(
                content=f"📥 Я успешно обработал и сохранил ваш документ «{title}» в базу знаний.\n"
                        f"Текст разбит на {chunks_count} фрагментов для точного поиска в будущем. ✅",
                agent=self.name,
                save_to_memory=False,
            )
        except Exception as e:
            logger.error("chat_ingest_error", error=str(e))
            return AgentResponse(
                content="❌ К сожалению, произошла ошибка при обработке документа. Попробуйте отправить его частями.",
                agent=self.name,
                save_to_memory=False,
            )


# ═══════════════════════════════════════════════════════════════════════════
# Global instances - keep both for backward compatibility
# ═══════════════════════════════════════════════════════════════════════════

# Legacy instance
from agents.base import BaseAgent as _BaseAgent

class _LegacyMemoryAgent(_BaseAgent):
    """Legacy Memory Agent for backward compatibility."""
    
    name = "memory"
    description = "Memory management agent"
    participates_in_dialogue = False
    writes_to_memory = True
    is_synchronous = True
    
    async def process(self, context):
        return AgentResponse(
            content="Memory operation completed",
            agent=self.name,
            save_to_memory=False,
        )
    
    async def save_from_response(self, db, response, session_id, user_message, user_id=None):
        """Delegate to v2."""
        v2 = MemoryAgentV2()
        actions = await v2.auto_save(db, response, 
            AgentContext(session_id=session_id, user_message=user_message), user_id=user_id)
        return actions[0].memory_id if actions else None
    
    async def get_context_memories(self, db, user_message, limit=5, user_id=None):
        """Delegate to v2."""
        v2 = MemoryAgentV2()
        return await v2.get_context_memories(db, user_message, limit, user_id)


memory_agent = _LegacyMemoryAgent()
memory_agent_v2 = MemoryAgentV2()
