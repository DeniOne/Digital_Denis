# Digital Den - LLM Providers
"""
Hybrid AI Architecture:
- openrouter.py: OpenRouter API (Claude, GPT, DeepSeek)
- gemini.py: Google Gemini API
- groq.py: Groq API (fast inference)
- llm_selector.py: Unified model selector by role
- model_router.py: Task classifier for model selection
"""

from llm.llm_selector import llm_selector, ModelRole, LLMSelector
from llm.model_router import model_router, TaskCategory, ModelRouter

__all__ = [
    "llm_selector",
    "model_router", 
    "ModelRole",
    "TaskCategory",
    "LLMSelector",
    "ModelRouter",
]
