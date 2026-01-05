# Digital Den - LLM Providers
"""
Hybrid AI Architecture:
- openrouter.py: OpenRouter API (Claude, GPT, DeepSeek)
- gemini.py: Google Gemini API
- groq.py: Groq API (fast inference)
- llm_selector.py: Unified model selector by role
- model_router.py: Task classifier for model selection

Usage:
    from llm.llm_selector import llm_selector, ModelRole
    from llm.model_router import model_router, TaskCategory
    from llm.gemini_cli_provider import gemini_cli
"""
