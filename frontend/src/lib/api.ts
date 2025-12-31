/**
 * Digital Denis — Full API Client
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Complete API client for all backend endpoints.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// Types
export interface MemoryItem {
  id: string;
  item_type: string;
  content: string;
  summary?: string;
  confidence?: number;
  source?: string;
  topics: TopicRef[];
  created_at: string;
  status: string;
}

export interface TopicRef {
  id: string;
  name: string;
  confidence: number;
}

export interface Topic {
  id: string;
  name: string;
  parent_id?: string;
  level: number;
  is_active: boolean;
  item_count: number;
  children: Topic[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  size: number;
  color: string;
  x?: number;
  y?: number;
  cluster?: number;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  weight: number;
  style: string;
  color: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters: { id: number; count: number }[];
  metadata: {
    total_nodes: number;
    total_edges: number;
    period_days: number;
  };
}

export interface Anomaly {
  id: string;
  anomaly_type: string;
  severity: string;
  title: string;
  interpretation?: string;
  suggested_action?: string;
  topic_id?: string;
  baseline_value?: number;
  current_value?: number;
  deviation_percent?: number;
  status: string;
  detected_at: string;
}

export interface CognitiveHealth {
  overall_score: number;
  decision_quality: number;
  memory_diversity: number;
  thinking_consistency: number;
  active_topics: number;
  total_memories: number;
  anomalies_count: number;
  last_activity: string;
}

export interface TopicTrend {
  topic_id: string;
  topic_name: string;
  current_count: number;
  previous_count: number;
  change_percent: number;
  trend: string;
}

export interface AnalyticsSummary {
  total_memories: number;
  by_type: Record<string, number>;
  top_topics: { id: string; name: string; count: number }[];
  streak: number;
  period_days: number;
}

export interface ActivityPoint {
  date: string;
  count: number;
}

export interface MoodData {
  date: string;
  mood: number;
  count: number;
}

export interface MessageResponse {
  response: string;
  agent: string;
  memory_saved: boolean;
  session_id: string;
  thinking_time_ms?: number;
}

export interface MemoryFilters {
  item_type?: string;
  topic_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface GraphParams {
  topic_id?: string;
  node_types?: string;
  days?: number;
  max_nodes?: number;
}

// Schedule Types
export interface ScheduleItem {
  id: string;
  item_type: 'event' | 'task' | 'reminder' | 'recurring';
  title: string;
  description?: string;
  start_at?: string;
  end_at?: string;
  due_at?: string;
  status: string;
}

export interface ScheduleListResponse {
  items: ScheduleItem[];
  date: string;
}

// API Client
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Error handling
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.message);
    throw error;
  }
);

// Messages API
export const messagesApi = {
  send: async (content: string, sessionId?: string, mode = 'fast'): Promise<MessageResponse> => {
    const { data } = await client.post('/messages', { content, session_id: sessionId, mode });
    return data;
  },

  getHistory: async (sessionId: string) => {
    const { data } = await client.get(`/messages/session/${sessionId}`);
    return data;
  },

  listSessions: async (limit = 20) => {
    const { data } = await client.get('/messages/sessions', { params: { limit } });
    return data;
  },

  endSession: async (sessionId: string) => {
    const { data } = await client.post(`/messages/session/${sessionId}/end`);
    return data;
  },
};

// Memory API
export const memoryApi = {
  list: async (filters: MemoryFilters = {}) => {
    const { data } = await client.get('/memory', { params: filters });
    return data;
  },

  get: async (id: string): Promise<MemoryItem> => {
    const { data } = await client.get(`/memory/${id}`);
    return data;
  },

  search: async (query: string, types?: string[], limit = 20) => {
    const { data } = await client.post('/memory/search', { query, types, limit });
    return data;
  },

  create: async (item: { item_type: string; content: string; summary?: string; topic_ids?: string[] }) => {
    const { data } = await client.post('/memory', item);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await client.delete(`/memory/${id}`);
    return data;
  },

  stats: async () => {
    const { data } = await client.get('/memory/stats/summary');
    return data;
  },
};

// Topics API
export const topicsApi = {
  list: async (parentId?: string) => {
    const { data } = await client.get('/topics', { params: { parent_id: parentId } });
    return data;
  },

  tree: async (): Promise<Topic[]> => {
    const { data } = await client.get('/topics/tree');
    return data;
  },

  get: async (id: string): Promise<Topic> => {
    const { data } = await client.get(`/topics/${id}`);
    return data;
  },

  activity: async (id: string) => {
    const { data } = await client.get(`/topics/${id}/activity`);
    return data;
  },

  trends: async (): Promise<TopicTrend[]> => {
    const { data } = await client.get('/topics/stats/trends');
    return data;
  },

  activeTopics: async () => {
    const { data } = await client.get('/topics/stats/activity');
    return data;
  },
};

// Graph API
export const graphApi = {
  get: async (params: GraphParams = {}): Promise<GraphData> => {
    const { data } = await client.get('/mindmap', { params });
    return data;
  },

  getNeighbors: async (nodeId: string, depth = 1): Promise<GraphData> => {
    const { data } = await client.get(`/mindmap/node/${nodeId}/neighbors`, { params: { depth } });
    return data;
  },

  buildConnections: async (memoryIds: string[]) => {
    const { data } = await client.post('/mindmap/build-connections', { memory_ids: memoryIds });
    return data;
  },

  stats: async () => {
    const { data } = await client.get('/mindmap/stats');
    return data;
  },
};

// CAL / Analytics API
export const analyticsApi = {
  getSummary: async (userId: string, days = 30): Promise<AnalyticsSummary> => {
    const { data } = await client.get('/analytics/summary', { params: { user_id: userId, days } });
    return data;
  },

  getActivity: async (userId: string, days = 30): Promise<ActivityPoint[]> => {
    const { data } = await client.get('/analytics/activity', { params: { user_id: userId, days } });
    return data;
  },

  getHeatmap: async (userId: string): Promise<ActivityPoint[]> => {
    const { data } = await client.get('/analytics/heatmap', { params: { user_id: userId } });
    return data;
  },

  getTrends: async (userId: string, days = 30, limit = 10): Promise<TopicTrend[]> => {
    const { data } = await client.get('/analytics/trends', { params: { user_id: userId, days, limit } });
    return data;
  },

  getGraph: async (params: GraphParams = {}) => {
    const { data } = await client.get('/cal/graph', { params });
    return data;
  },

  getMood: async (userId: string, days = 30): Promise<MoodData[]> => {
    const { data } = await client.get('/analytics/mood', { params: { user_id: userId, days } });
    return data;
  },

  getAnomalies: async (status = 'new', limit = 20): Promise<Anomaly[]> => {
    const { data } = await client.get('/anomalies', { params: { status, limit } });
    return data;
  },

  acknowledgeAnomaly: async (id: string) => {
    const { data } = await client.post(`/anomalies/${id}/acknowledge`);
    return data;
  },

  resolveAnomaly: async (id: string, note?: string) => {
    const { data } = await client.post(`/anomalies/${id}/resolve`, { resolution_note: note });
    return data;
  },

  dismissAnomaly: async (id: string) => {
    const { data } = await client.post(`/anomalies/${id}/dismiss`);
    return data;
  },

  runDetection: async (baselineDays = 30, currentDays = 7) => {
    const { data } = await client.post('/anomalies/detect', null, {
      params: { baseline_days: baselineDays, current_days: currentDays }
    });
    return data;
  },

  getHealth: async (): Promise<CognitiveHealth> => {
    const { data } = await client.get('/health/cognitive');
    return data;
  },

  anomalyStats: async () => {
    const { data } = await client.get('/anomalies/stats');
    return data;
  },
};

// Decisions API
export const decisionsApi = {
  analyze: async (decisionId: string) => {
    const { data } = await client.post(`/decisions/${decisionId}/analyze`);
    return data;
  },

  getAnalysis: async (decisionId: string) => {
    const { data } = await client.get(`/decisions/${decisionId}/analysis`);
    return data;
  },

  list: async (limit = 20, minScore?: number, maxScore?: number) => {
    const { data } = await client.get('/decisions', { params: { limit, min_score: minScore, max_score: maxScore } });
    return data;
  },

  stats: async () => {
    const { data } = await client.get('/decisions/stats');
    return data;
  },
};

// Health API
export const healthApi = {
  system: async () => {
    const { data } = await client.get('/health');
    return data;
  },

  cognitive: async (): Promise<CognitiveHealth> => {
    const { data } = await client.get('/health/cognitive');
    return data;
  },

  ping: async () => {
    const { data } = await client.get('/health/ping');
    return data;
  },
};

// Notifications API
export const notificationsApi = {
  getVapidKey: async () => {
    const { data } = await client.get('/notifications/vapid-public-key');
    return data;
  },

  subscribe: async (subscription: { endpoint: string; keys: { p256dh: string; auth: string } }) => {
    const { data } = await client.post('/notifications/subscribe', subscription);
    return data;
  },

  unsubscribe: async (endpoint: string) => {
    const { data } = await client.delete('/notifications/unsubscribe', { params: { endpoint } });
    return data;
  },

  test: async () => {
    const { data } = await client.post('/notifications/test');
    return data;
  }
};

// Settings Types
export interface BehaviorSettings {
  ai_role: string;
  thinking_depth: string;
  response_style: string;
  confrontation_level: string;
}

export interface AutonomySettings {
  initiative_level: string;
  intervention_frequency: string;
  allowed_actions: string[];
}

export interface MemorySettings {
  save_policy: string;
  auto_archive_days: number;
  memory_trust_level: string;
  saved_types: string[];
}

export interface AnalyticsSettings {
  analytics_types: string[];
  analytics_aggressiveness: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  behavior: BehaviorSettings;
  autonomy: AutonomySettings;
  memory: MemorySettings;
  analytics: AnalyticsSettings;
  created_at?: string;
  updated_at?: string;
}

export interface Rule {
  id: string;
  scope: 'global' | 'context';
  trigger: 'always' | 'topic' | 'mode' | 'session';
  instruction: string;
  priority: 'low' | 'normal' | 'high';
  is_active: boolean;
  context_topic_id?: string;
  context_mode?: string;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface RuleCreate {
  instruction: string;
  scope?: string;
  trigger?: string;
  priority?: string;
  context_topic_id?: string;
  context_mode?: string;
}

export interface RuleUpdate {
  instruction?: string;
  priority?: string;
  is_active?: boolean;
  context_topic_id?: string;
  context_mode?: string;
  sort_order?: number;
}

// Settings API
export const settingsApi = {
  get: async (): Promise<UserSettings> => {
    const { data } = await client.get('/settings');
    return data;
  },

  update: async (settings: Partial<UserSettings>): Promise<UserSettings> => {
    const { data } = await client.put('/settings', settings);
    return data;
  },

  updateBehavior: async (behavior: Partial<BehaviorSettings>) => {
    const { data } = await client.patch('/settings/behavior', behavior);
    return data;
  },

  updateAutonomy: async (autonomy: Partial<AutonomySettings>) => {
    const { data } = await client.patch('/settings/autonomy', autonomy);
    return data;
  },

  updateMemory: async (memory: Partial<MemorySettings>) => {
    const { data } = await client.patch('/settings/memory', memory);
    return data;
  },

  updateAnalytics: async (analytics: Partial<AnalyticsSettings>) => {
    const { data } = await client.patch('/settings/analytics', analytics);
    return data;
  },
};

// Rules API
export const rulesApi = {
  list: async (scope?: string): Promise<Rule[]> => {
    const { data } = await client.get('/settings/rules', { params: { scope } });
    return data;
  },

  get: async (id: string): Promise<Rule> => {
    const { data } = await client.get(`/settings/rules/${id}`);
    return data;
  },

  create: async (rule: RuleCreate): Promise<Rule> => {
    const { data } = await client.post('/settings/rules', rule);
    return data;
  },

  update: async (id: string, rule: RuleUpdate): Promise<Rule> => {
    const { data } = await client.put(`/settings/rules/${id}`, rule);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await client.delete(`/settings/rules/${id}`);
    return data;
  },

  toggle: async (id: string) => {
    const { data } = await client.patch(`/settings/rules/${id}/toggle`);
    return data;
  },
};

// Schedule API
export const scheduleApi = {
  getToday: async (): Promise<ScheduleListResponse> => {
    const { data } = await client.get('/schedule/today');
    return data;
  },

  getRange: async (dateFrom: string, dateTo: string, includeCompleted = false): Promise<ScheduleListResponse> => {
    const { data } = await client.get('/schedule/range', {
      params: { date_from: dateFrom, date_to: dateTo, include_completed: includeCompleted }
    });
    return data;
  },

  createEvent: async (event: { title: string; start_at: string; end_at?: string; duration_minutes?: number; description?: string }) => {
    const { data } = await client.post('/schedule/events', event);
    return data;
  },

  createTask: async (task: { title: string; due_at: string; description?: string }) => {
    const { data } = await client.post('/schedule/tasks', task);
    return data;
  },

  createReminder: async (reminder: { title: string; remind_at: string; description?: string }) => {
    const { data } = await client.post('/schedule/reminders', reminder);
    return data;
  },

  completeItem: async (id: string) => {
    const { data } = await client.patch(`/schedule/items/${id}/complete`);
    return data;
  },

  skipItem: async (id: string) => {
    const { data } = await client.patch(`/schedule/items/${id}/skip`);
    return data;
  },

  confirmReminder: async (id: string) => {
    const { data } = await client.post(`/reminders/${id}/done`);
    return data;
  },

  snoozeReminder: async (id: string, minutes = 15) => {
    const { data } = await client.post(`/reminders/${id}/snooze`, null, { params: { minutes } });
    return data;
  },

  skipReminder: async (id: string) => {
    const { data } = await client.post(`/reminders/${id}/skip`);
    return data;
  },
};

// Export combined API
export const api = {
  messages: messagesApi,
  memory: memoryApi,
  topics: topicsApi,
  graph: graphApi,
  analytics: analyticsApi,
  decisions: decisionsApi,
  health: healthApi,
  notifications: notificationsApi,
  settings: settingsApi,
  rules: rulesApi,
  schedule: scheduleApi,
};

export default client;

