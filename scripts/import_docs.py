"""
Digital Den — CLI Document Importer
===========================================================================

Utility script to import text/markdown documents into the system's memory.
Usage: python scripts/import_docs.py --path /path/to/docs --user-id UUID
"""

import os
import sys
import asyncio
import argparse
from uuid import UUID

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from db.database import async_session_maker
from core.document_service import document_service
from memory.models import User
from sqlalchemy import select

async def run_import(path: str, user_id_str: str):
    user_id = UUID(user_id_str)
    
    async with async_session_maker() as db:
        # 1. Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ Error: User {user_id} not found in database.")
            return

        print(f"🚀 Starting import for user: {user.username or user.telegram_id}")
        
        # 2. Check if path is file or folder
        if os.path.isfile(path):
            count = await document_service.ingest_file(db, user_id, path)
            print(f"✅ Imported file: {os.path.basename(path)} ({count} chunks)")
        elif os.path.isdir(path):
            print(f"📁 Scanning folder: {path}...")
            results = await document_service.ingest_folder(db, user_id, path)
            total_chunks = sum(results.values())
            print(f"\n✅ Import complete!")
            print(f"📂 Files processed: {len(results)}")
            print(f"🧩 Total chunks indexed: {total_chunks}")
            for file, count in results.items():
                print(f"  - {file}: {count} chunks")
        else:
            print(f"❌ Error: Path {path} is not a valid file or directory.")
            return

        await db.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Den Document Importer")
    parser.add_argument("--path", required=True, help="Path to file or folder")
    parser.add_argument("--user-id", required=True, help="UUID of the user")
    
    args = parser.parse_args()
    
    asyncio.run(run_import(args.path, args.user_id))
