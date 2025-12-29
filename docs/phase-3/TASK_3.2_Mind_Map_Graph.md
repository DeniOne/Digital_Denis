# 🗺️ TASK 3.2 — Mind Map Graph Model

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 3.1

---

## 📋 Чеклист реализации (v1.0)

- [x] Создать backend/analytics/graphs.py
- [x] Реализовать GraphBuilder
- [x] Создать таблицы graph_nodes, graph_edges
- [x] Реализовать find_connections() с LLM
- [x] API endpoint /graph
- [x] Написать unit-тесты

---

## 🎯 Цель

Описать графовую модель майнд-карт: типы узлов, связей, правила генерации.

---

## 📦 Артефакты

### 1. Graph Schema

#### Типы узлов (Nodes)

| Тип | Описание | Иконка | Атрибуты |
|-----|----------|--------|----------|
| `idea` | Идея, гипотеза, мысль | 💡 | content, confidence, created_at |
| `decision` | Принятое решение | ✅ | content, structured_data, confidence |
| `insight` | Осознание, вывод | 💎 | content, source, confidence |
| `topic` | Тематический кластер | 📁 | name, item_count |
| `fact` | Факт, данные | 📊 | content, source, verified |

#### Типы связей (Edges)

| Тип | Описание | Направление | Визуализация |
|-----|----------|-------------|--------------|
| `depends_on` | A зависит от B | A → B | Сплошная стрелка |
| `contradicts` | A противоречит B | A ↔ B | Красная пунктирная |
| `evolves_from` | A эволюция B | A → B | Синяя стрелка |
| `reinforces` | A усиливает B | A → B | Зелёная стрелка |
| `belongs_to` | A принадлежит теме B | A → B | Серая тонкая |

---

### 2. Graph Generation Rules

```python
class GraphBuilder:
    """Mind Map graph construction"""
    
    # Thresholds
    MIN_SIMILARITY_FOR_EDGE = 0.7
    MIN_CONFIDENCE_FOR_NODE = 0.5
    
    async def find_connections(
        self, 
        new_items: List[MemoryItem]
    ) -> List[GraphEdge]:
        """Find connections between new and existing items"""
        
        edges = []
        
        for item in new_items:
            # 1. Find semantically similar items
            similar = await self.semantic_search(
                item.content, 
                limit=10,
                min_score=self.MIN_SIMILARITY_FOR_EDGE
            )
            
            # 2. Determine relationship type
            for sim_item in similar:
                edge_type = await self._determine_edge_type(item, sim_item)
                if edge_type:
                    edges.append(GraphEdge(
                        source_id=item.id,
                        target_id=sim_item.id,
                        edge_type=edge_type,
                        confidence=sim_item.similarity_score
                    ))
            
            # 3. Check for contradictions in decisions
            if item.item_type == 'decision':
                contradictions = await self._find_contradictions(item)
                for c in contradictions:
                    edges.append(GraphEdge(
                        source_id=item.id,
                        target_id=c.id,
                        edge_type='contradicts',
                        confidence=c.contradiction_score
                    ))
        
        return edges
    
    async def _determine_edge_type(
        self, 
        source: MemoryItem, 
        target: MemoryItem
    ) -> Optional[str]:
        """Use LLM to determine relationship type"""
        
        prompt = f"""
        Determine the relationship between these two items:
        
        Item A ({source.item_type}): {source.content[:200]}
        Item B ({target.item_type}): {target.content[:200]}
        
        Possible relationships:
        - depends_on: A requires or builds upon B
        - evolves_from: A is an evolution/refinement of B
        - reinforces: A supports or strengthens B
        - contradicts: A conflicts with B
        - none: No meaningful relationship
        
        Return only the relationship type.
        """
        
        result = await self.llm.complete(prompt, model="claude-3-haiku")
        return result.strip() if result.strip() != 'none' else None
```

---

### 3. Graph Storage

```sql
-- Nodes (linked to memory items)
CREATE TABLE graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memory_items(id) ON DELETE CASCADE,
    node_type VARCHAR(50) NOT NULL,
    label TEXT,
    
    -- Visual properties
    size FLOAT DEFAULT 1.0,
    color VARCHAR(50),
    
    -- Computed metrics
    degree INTEGER DEFAULT 0,  -- number of connections
    centrality FLOAT,  -- importance in graph
    cluster_id UUID,  -- community detection
    
    -- Position (if saved)
    x FLOAT,
    y FLOAT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Edges
CREATE TABLE graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
    edge_type VARCHAR(50) NOT NULL,
    
    -- Weight and confidence
    weight FLOAT DEFAULT 1.0,
    confidence FLOAT DEFAULT 0.5,
    
    -- Visual properties
    style VARCHAR(50) DEFAULT 'solid',
    color VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_id, target_id, edge_type)
);

-- Indexes
CREATE INDEX idx_graph_nodes_memory ON graph_nodes(memory_id);
CREATE INDEX idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX idx_graph_edges_target ON graph_edges(target_id);
```

---

### 4. Graph API

```python
class MindMapService:
    async def get_graph(
        self,
        topic_id: UUID = None,
        node_types: List[str] = None,
        days: int = 30,
        max_nodes: int = 100
    ) -> GraphData:
        """Get graph data for visualization"""
        
        # Build query
        query = self._build_query(topic_id, node_types, days)
        
        # Get nodes
        nodes = await self.db.fetch(query, limit=max_nodes)
        node_ids = [n.id for n in nodes]
        
        # Get edges between these nodes
        edges = await self.db.fetch_edges(node_ids)
        
        return GraphData(
            nodes=[self._format_node(n) for n in nodes],
            edges=[self._format_edge(e) for e in edges]
        )
    
    def _format_node(self, node: GraphNode) -> dict:
        return {
            "id": str(node.id),
            "label": node.label[:50],
            "type": node.node_type,
            "size": node.size,
            "color": self._get_color(node.node_type),
            "data": {
                "memory_id": str(node.memory_id),
                "created_at": node.created_at.isoformat()
            }
        }
```

---

## ✅ Критерии завершения

- [x] Все типы узлов описаны
- [x] Все типы связей описаны
- [x] Правила генерации формализованы
- [x] Confidence threshold определён

---

## 📎 Связанные документы

- [TASK 3.1 — CAL Architecture](./TASK_3.1_CAL_Architecture.md)
- [TASK 5.3 — Visualization Spec](../phase-5/TASK_5.3_Visualization_Spec.md)
