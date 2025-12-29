# 🖥️ TASK 5.1 — Frontend Architecture

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 4.1

---

## 📋 Чеклист реализации

- [x] npx create-next-app frontend/
- [x] Настроить Tailwind CSS
- [x] Добавить shadcn/ui компоненты
- [x] Создать lib/api.ts (API client)
- [x] Настроить React Query
- [x] Создать Zustand store
- [x] Все страницы роутинга готовы

---

## 🎯 Цель

Спроектировать архитектуру фронтенда: страницы, состояние, API.

---

## 📦 Артефакт: Frontend Architecture Doc

### Технологический стек

| Технология | Назначение |
|------------|------------|
| Next.js 14 | App Router, SSR |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| shadcn/ui | UI components |
| Zustand | State management |
| React Query | API caching |
| D3.js | Custom charts |
| Cytoscape.js | Graph visualization |
| Recharts | Standard charts |

---

### Структура страниц (App Router)

| Route | Компонент | Описание |
|-------|-----------|----------|
| `/` | Dashboard | Overview + Quick stats |
| `/memory` | MemoryExplorer | Browse/search memory |
| `/memory/[id]` | MemoryDetail | Single item view |
| `/topics` | TopicExplorer | Topic tree + trends |
| `/mindmap` | MindMapView | Interactive graph |
| `/health` | CognitiveHealth | Anomalies + reports |
| `/settings` | Settings | Configuration |

---

### State Management (Zustand)

```typescript
// store/index.ts
interface AppState {
  // Session
  sessionId: string | null;
  
  // Memory (cached)
  memories: MemoryItem[];
  loadingMemories: boolean;
  
  // Topics
  topicTree: TopicNode[];
  activeTopic: string | null;
  
  // Graph
  graphData: GraphData | null;
  selectedNode: string | null;
  
  // Anomalies
  anomalies: Anomaly[];
  unreadCount: number;
  
  // Actions
  setSession: (id: string) => void;
  fetchMemories: (filters: MemoryFilters) => Promise<void>;
  selectTopic: (id: string) => void;
  acknowledgeAnomaly: (id: string) => Promise<void>;
}
```

---

### API Client (React Query)

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export const api = {
  memory: {
    list: (filters: MemoryFilters) => 
      fetch(`${API_BASE}/memory?${new URLSearchParams(filters)}`),
    get: (id: string) => 
      fetch(`${API_BASE}/memory/${id}`),
    search: (query: string) => 
      fetch(`${API_BASE}/memory/search`, { 
        method: 'POST', 
        body: JSON.stringify({ query }) 
      }),
  },
  topics: {
    tree: () => fetch(`${API_BASE}/topics/tree`),
    trends: () => fetch(`${API_BASE}/topics/trends`),
  },
  graph: {
    get: (params: GraphParams) => 
      fetch(`${API_BASE}/graph?${new URLSearchParams(params)}`),
  },
  analytics: {
    anomalies: () => fetch(`${API_BASE}/analytics/anomalies`),
    health: () => fetch(`${API_BASE}/analytics/health`),
  },
};

// hooks/useMemory.ts
export function useMemories(filters: MemoryFilters) {
  return useQuery({
    queryKey: ['memories', filters],
    queryFn: () => api.memory.list(filters),
    staleTime: 5 * 60 * 1000, // 5 min
  });
}
```

---

### Caching Strategy

| Resource | Stale Time | Cache Time | Refresh |
|----------|------------|------------|---------|
| Memory list | 5 min | 10 min | On mutation |
| Memory detail | 10 min | 30 min | Manual |
| Topics tree | 10 min | 30 min | On mutation |
| Graph data | 5 min | 10 min | On filter change |
| Anomalies | 1 min | 5 min | Polling |

---

### Component Structure

```
components/
├── ui/                  # shadcn/ui (Button, Card, etc.)
├── layout/
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   └── Shell.tsx
├── memory/
│   ├── MemoryCard.tsx
│   ├── MemoryList.tsx
│   └── MemorySearch.tsx
├── topics/
│   ├── TopicTree.tsx
│   └── TopicHeatmap.tsx
├── graphs/
│   ├── MindMapGraph.tsx
│   └── GraphControls.tsx
└── analytics/
    ├── TrendChart.tsx
    ├── AnomalyAlert.tsx
    └── HealthScore.tsx
```

---

## ✅ Критерии завершения

- [x] Все страницы описаны
- [x] State management спроектирован
- [x] API интеграция определена
- [x] Caching strategy установлена

---

## 📎 Связанные документы

- [TASK 4.1 — API Contracts](../phase-4/TASK_4.1_API_Contracts.md)
- [TASK 5.2 — UI Wireframes](./TASK_5.2_UI_Wireframes.md)
