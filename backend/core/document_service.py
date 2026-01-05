"""
Digital Den — Document Ingestion Service
===========================================================================

Service for processing, chunking and indexing large documents into memory.
"""

import os
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from memory.models import MemoryItem
from memory.semantic import semantic_memory
from core.encryption import encryptor
from core.logging import get_logger

logger = get_logger(__name__)

class DocumentService:
    """
    Handles ingestion of documents and folders into the Knowledge Base.
    """
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        Simplified version: splits by sentences/paragraphs where possible.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If we're not at the end, try to find a natural break (paragraph or sentence)
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break != -1 and para_break > start + (self.chunk_size // 2):
                    end = para_break + 2
                else:
                    # Look for sentence break
                    sent_break = text.rfind(". ", start, end)
                    if sent_break != -1 and sent_break > start + (self.chunk_size // 2):
                        end = sent_break + 2
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # Move start forward with overlap
            start = end - self.chunk_overlap
            if start < 0: start = 0
            # Safety check to avoid infinite loop
            if start >= end: start = end
            
        return chunks

    async def ingest_text(
        self,
        db: AsyncSession,
        user_id: UUID,
        text: str,
        title: str,
        source_type: str = "document",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Process a block of text, chunk it, and save to memory.
        Returns count of chunks created.
        """
        chunks = self.chunk_text(text)
        logger.info("ingesting_document", title=title, chunks=len(chunks))
        
        chunk_ids = []
        for i, chunk_content in enumerate(chunks):
            # Format content with context
            content_with_meta = f"Источник: {title}\nЧасть {i+1}/{len(chunks)}\n\n{chunk_content}"
            
            # Save as MemoryItem
            item = MemoryItem(
                id=uuid4(),
                user_id=user_id,
                item_type="knowledge",
                content=encryptor.encrypt(content_with_meta),
                summary=encryptor.encrypt(f"Фрагмент документа '{title}'"),
                structured_data={
                    "source": title,
                    "source_type": source_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **(metadata or {})
                },
                status="active",
                confidence=1.0, # Knowledge is usually verified
            )
            db.add(item)
            chunk_ids.append(item.id)
            
        await db.flush()
        
        # Index everything for semantic search
        for cid in chunk_ids:
            # Note: semantic_memory.index decrypts before sending to LLM
            await semantic_memory.index(db, cid)
            
        logger.info("document_ingested", title=title, chunks_saved=len(chunk_ids))
        return len(chunk_ids)

    async def ingest_file(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        file_path: str
    ) -> int:
        """Read and ingest a single text file."""
        if not os.path.exists(file_path):
            logger.error("file_not_found", path=file_path)
            return 0
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            title = os.path.basename(file_path)
            return await self.ingest_text(
                db=db,
                user_id=user_id,
                text=content,
                title=title,
                source_type="file",
                metadata={"file_path": file_path}
            )
        except Exception as e:
            logger.error("file_ingest_error", path=file_path, error=str(e))
            return 0

    async def ingest_folder(
        self,
        db: AsyncSession,
        user_id: UUID,
        folder_path: str,
        extensions: List[str] = [".txt", ".md"]
    ) -> Dict[str, int]:
        """Recursively ingest all matching files in a folder."""
        results = {}
        if not os.path.isdir(folder_path):
            logger.error("folder_not_found", path=folder_path)
            return results
            
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, file)
                    count = await self.ingest_file(db, user_id, full_path)
                    results[file] = count
                    
        return results

# Global instance
document_service = DocumentService()
