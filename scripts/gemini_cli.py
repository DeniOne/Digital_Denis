#!/usr/bin/env python3
"""
Digital Den — Gemini CLI
═══════════════════════════════════════════════════════════════════════════

Console interface for Gemini LLM.
Usage: python scripts/gemini_cli.py "analyze these logs..." [model_name]
"""

import sys
import asyncio
import os

# Add backend to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from llm.gemini import gemini
from llm.base import LLMMessage


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/gemini_cli.py <prompt> [model]")
        sys.exit(1)
        
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🤖 Gemini {f'({model})' if model else ''} is thinking...")
    print("─" * 40)
    
    try:
        response = await gemini.complete_simple(
            prompt=prompt,
            system="Ты — экспертный ИИ-ассистент системы Digital Den. "
                   "Твоя задача — помогать в самоанализе, архитектуре и решении сложных задач (Kaizen). "
                   "Отвечай глубоко и структурировано.",
            model=model
        )
        
        print(response)
        print("─" * 40)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
