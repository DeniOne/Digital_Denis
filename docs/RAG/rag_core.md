rag_core.md
Purpose

This document defines the architecture, data model, and operational principles of the RAG 2.0 system used in Digital Denis.

Core Principles

Memory is typed and contextual.

Retrieval is intent-aware.

Time matters.

Not all memories are facts.

Improvement is measurable (Kaizen).

Architecture Overview

The system consists of:

Core Orchestrator

Intent Classifier

Hybrid Retrieval Engine

Context Assembler

LLM Core Agent

Kaizen Engine

Each request passes through intent detection, smart retrieval, framed context assembly, and post-response evaluation.

Memory Types
Type	Usage
fact	Verified information
decision	User-made decisions
principle	Long-term guiding rules
rule	Explicit operational constraints
hypothesis	Unconfirmed assumptions
reflection	Thoughts & analysis
emotion	Emotional states
failure	Mistakes and errors
Retrieval Logic

Final relevance score:

score = semantic_similarity
      × memory_type_weight
      × intent_weight
      × time_decay

Context Framing Rules

Principles override opinions.

Facts override hypotheses.

Conflicts must be surfaced explicitly.

Hypotheses must be marked as uncertain.

Kaizen Engine

The system tracks:

memory usage frequency

outcome effectiveness

trend improvement per dimension

The goal is continuous self-optimization.

## Conversation State Layer

The Conversation State Layer is a first-class component of RAG 2.0.
It provides explicit dialog state tracking and is the primary source
of conversational context, especially in low-bandwidth channels
such as Telegram.

See:
- conversation_state_schema.md
- state_extractor_prompt.md
- telegram_adapter_flow.md

---

## Статус

RAG 2.0 defines the foundation for an agentic, self-improving AI assistant.