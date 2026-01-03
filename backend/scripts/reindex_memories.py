"""
Digital Den — Re-indexing Script
═══════════════════════════════════════════════════════════════════════════

Re-indexes all active memory items using the optimized embedding service.
"""

import asyncio
import argparse
from uuid import UUID

from db.database import async_session
from memory.semantic import semantic_memory

async def reindex(batch_size: int = 20, limit: int = None):
    print(f"🚀 Starting re-indexing (batch size: {batch_size}, limit: {limit})...")
    
    async with async_session() as db:
        total = await semantic_memory.reindex_all(db)
        print(f"✅ Success! Indexed {total} memories.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-index memories for Vector DB optimization.")
    parser.add_argument("--batch", type=int, default=20, help="Batch size for embeddings")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of items to index")
    
    args = parser.parse_args()
    
    asyncio.run(reindex(batch_size=args.batch, limit=args.limit))
