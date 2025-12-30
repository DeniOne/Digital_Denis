"""
Digital Denis — Sentiment Analysis Service
═══════════════════════════════════════════════════════════════════════════

Simple sentiment analysis engine using keyword matching for MVP.
Planned upgrade: TinyBERT or local LLM for better accuracy.
"""

from typing import List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from memory.models import MemoryItem

# ═══════════════════════════════════════════════════════════════════════════
# Keywords (MVP)
# ═══════════════════════════════════════════════════════════════════════════

POSITIVE_WORDS = {
    "успех", "победа", "радость", "отлично", "хорошо", "люблю", "нравится",
    "круто", "прекрасно", "супер", "счастье", "вдохновение", "энергия",
    "получилось", "смог", "достиг", "выполнил", "решил", "полезно",
    "success", "happy", "great", "good", "love", "amazing", "win"
}

NEGATIVE_WORDS = {
    "провал", "ошибка", "грусть", "плохо", "ужас", "ненавижу", "бесит",
    "проблема", "сложно", "устал", "боль", "страх", "тревога",
    "не получилось", "не смог", "потерял", "зря", "скучно",
    "fail", "sad", "bad", "hate", "error", "problem", "tired"
}

class SentimentService:
    def analyze_text(self, text: str) -> float:
        """
        Analyze text sentiment.
        Returns score from -1.0 (negative) to 1.0 (positive).
        """
        if not text:
            return 0.0
            
        text_lower = text.lower()
        words = text_lower.split()
        
        score = 0.0
        
        for word in words:
            # Simple stemming-like match
            for pos in POSITIVE_WORDS:
                if pos in word:
                    score += 0.5
                    break
            
            for neg in NEGATIVE_WORDS:
                if neg in word:
                    score -= 0.5
                    break
        
        # Clamp score between -1 and 1
        return max(-1.0, min(1.0, score))

    async def get_daily_mood(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> List[Dict]:
        """
        Calculate average daily mood based on memory content.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Fetch all memories for the period
        result = await db.execute(
            select(
                func.date(MemoryItem.created_at).label("date"),
                MemoryItem.content
            )
            .where(
                and_(
                    MemoryItem.user_id == user_id,
                    MemoryItem.created_at >= since,
                    MemoryItem.status == 'active'
                )
            )
            .order_by("date")
        )
        
        rows = result.fetchall()
        
        daily_scores = {}
        daily_counts = {}
        
        for row in rows:
            date_str = str(row.date)
            sentiment = self.analyze_text(row.content)
            
            daily_scores[date_str] = daily_scores.get(date_str, 0.0) + sentiment
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
        # Average the scores
        chart_data = []
        current_date = since.date()
        today = datetime.utcnow().date()
        
        while current_date <= today:
            date_str = str(current_date)
            count = daily_counts.get(date_str, 0)
            avg_score = (daily_scores.get(date_str, 0.0) / count) if count > 0 else 0.0
            
            chart_data.append({
                "date": date_str,
                "mood": round(avg_score, 2),
                "count": count
            })
            current_date += timedelta(days=1)
            
        return chart_data

sentiment_service = SentimentService()
