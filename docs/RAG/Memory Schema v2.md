Memory Schema v2 (Database Design)
2.1. Таблица memories
CREATE TABLE memories (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,

  embedding VECTOR(1536),

  memory_type VARCHAR(32) NOT NULL,
  confidence_level VARCHAR(16) NOT NULL,

  topics TEXT[],

  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP,

  source VARCHAR(32), -- user, system, agent
  related_to UUID[],  -- связи между воспоминаниями

  usage_count INT DEFAULT 0,
  positive_outcomes INT DEFAULT 0,
  negative_outcomes INT DEFAULT 0,

  is_active BOOLEAN DEFAULT true
);

memory_type (ключевое!)
fact
decision
principle
rule
hypothesis
reflection
emotion
failure
task

confidence_level
high
medium
low
unknown

2.2. Индексы
-- Векторный поиск
CREATE INDEX idx_memories_embedding
ON memories
USING ivfflat (embedding vector_cosine_ops);

-- Полнотекстовый
CREATE INDEX idx_memories_fts
ON memories
USING gin (to_tsvector('russian', content));

-- Тип памяти
CREATE INDEX idx_memories_type
ON memories (memory_type);

-- Время
CREATE INDEX idx_memories_created_at
ON memories (created_at);

2.3. Таблица memory_events (метапамять)
CREATE TABLE memory_events (
  id UUID PRIMARY KEY,
  memory_id UUID REFERENCES memories(id),

  event_type VARCHAR(32), -- recalled, used, rejected
  outcome VARCHAR(16),    -- positive, neutral, negative

  created_at TIMESTAMP DEFAULT now()
);

2.4. Таблица kaizen_metrics
CREATE TABLE kaizen_metrics (
  id UUID PRIMARY KEY,

  dimension VARCHAR(32),
  score NUMERIC,

  context TEXT,
  created_at TIMESTAMP DEFAULT now()
);


Примеры dimension:

decision_quality
consistency
clarity_of_thought
execution
emotional_stability