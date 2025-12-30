"""
Digital Denis — Topic Generation Service
═══════════════════════════════════════════════════════════════════════════

Uses LLM to name clusters and extract keywords.
"""

import json
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import MemoryItem
from llm.groq import groq  # Preferred for speed/cost

class TopicNamingService:
    """
    Generates human-readable names and metadata for memory clusters.
    """
    
    async def generate_topic_metadata(
        self, 
        db: AsyncSession, 
        memory_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Takes a list of memory items and returns {name, description, keywords}.
        """
        # 1. Fetch memory contents (sample if too many)
        sample_ids = memory_ids[:10]
        stmt = select(MemoryItem.content).where(MemoryItem.id.in_(sample_ids))
        result = await db.execute(stmt)
        contents = [row[0] for row in result.fetchall()]
        
        if not contents:
            return {
                "name": "Unknown Topic",
                "description": "Auto-generated topic from memories",
                "keywords": []
            }
            
        combined_text = "\n---\n".join(contents[:1500]) # Limit context
        
        # 2. Call LLM
        prompt = f"""Ниже представлены несколько записей из дневника/памяти пользователя. 
Проанализируй их и придумай:
1. Краткое название темы (2-4 слова).
2. Краткое описание (1 предложение).
3. Список из 3-5 ключевых слов.

Записи:
{combined_text}

Ответ верни СТРОГО в формате JSON:
{{
  "name": "Название темы",
  "description": "Описание темы",
  "keywords": ["слово1", "слово2"]
}}

Язык: Русский.
"""

        try:
            response = await groq.complete_simple(prompt)
            # Basic JSON extraction from markdown if LLM includes it
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            data = json.loads(response.strip())
            return {
                "name": data.get("name", "Новая тема"),
                "description": data.get("description", ""),
                "keywords": data.get("keywords", [])
            }
        except Exception as e:
            print(f"Error generating topic naming: {e}")
            return {
                "name": "Авто-тема",
                "description": "Автоматически сгруппированные воспоминания",
                "keywords": []
            }

topic_naming_service = TopicNamingService()
