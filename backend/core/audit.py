"""
Digital Denis — Audit Service
═══════════════════════════════════════════════════════════════════════════

Service for recording audit logs for security and compliance.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import AuditLog
from core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for handling audit logs."""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[UUID],
        action: str,
        target_type: str = None,
        target_id: str = None,
        changes: Dict[str, Any] = None,
        meta_data: Dict[str, Any] = None,
    ) -> None:
        """
        Record a user action.
        
        Args:
            db: Database session
            user_id: ID of the user performing the action
            action: unique action identifier (e.g. "memory_create")
            target_type: type of entity affected (e.g. "memory_item")
            target_id: ID of the entity affected
            changes: dictionary of changes {"field": {"old": v, "new": v}}
            meta_data: additional context (ip, user_agent, etc.)
        """
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=str(target_id) if target_id else None,
                changes=changes or {},
                meta_data=meta_data or {},
            )
            
            db.add(audit_entry)
            # We don't commit here immediately to allow transaction bundling,
            # but usually audit logs should be committed even if main operation fails?
            # For now, we assume it's part of the main transaction.
            
            logger.info(
                "audit_log_created",
                action=action,
                user_id=str(user_id) if user_id else "system",
                target_type=target_type
            )
            
        except Exception as e:
            logger.error("audit_log_failed", error=str(e), action=action)
