/**
 * Digital Denis — React Query Hooks
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Custom hooks for data fetching with React Query.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    memoryApi,
    topicsApi,
    graphApi,
    analyticsApi,
    decisionsApi,
    healthApi,
    messagesApi,
    type MemoryFilters,
    type GraphParams,
} from './api';

// ═══════════════════════════════════════════════════════════════════════════
// Query Keys
// ═══════════════════════════════════════════════════════════════════════════

export const queryKeys = {
    memories: (filters?: MemoryFilters) => ['memories', filters] as const,
    memory: (id: string) => ['memory', id] as const,
    memoryStats: ['memory', 'stats'] as const,

    topicTree: ['topics', 'tree'] as const,
    topicTrends: ['topics', 'trends'] as const,
    topicActivity: (id: string) => ['topics', 'activity', id] as const,

    graph: (params?: GraphParams) => ['graph', params] as const,
    graphStats: ['graph', 'stats'] as const,

    anomalies: (status?: string) => ['anomalies', status] as const,
    anomalyStats: ['anomalies', 'stats'] as const,
    cognitiveHealth: ['health', 'cognitive'] as const,
    systemHealth: ['health', 'system'] as const,

    decisions: ['decisions'] as const,
    decisionAnalysis: (id: string) => ['decisions', 'analysis', id] as const,
    decisionStats: ['decisions', 'stats'] as const,

    sessions: ['sessions'] as const,
    sessionHistory: (id: string) => ['sessions', id] as const,
};

// ═══════════════════════════════════════════════════════════════════════════
// Memory Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useMemories(filters: MemoryFilters = { limit: 20, offset: 0 }) {
    return useQuery({
        queryKey: queryKeys.memories(filters),
        queryFn: () => memoryApi.list(filters),
        staleTime: 5 * 60 * 1000, // 5 min
    });
}

export function useMemory(id: string) {
    return useQuery({
        queryKey: queryKeys.memory(id),
        queryFn: () => memoryApi.get(id),
        staleTime: 10 * 60 * 1000, // 10 min
        enabled: !!id,
    });
}

export function useMemorySearch() {
    return useMutation({
        mutationFn: ({ query, types, limit }: { query: string; types?: string[]; limit?: number }) =>
            memoryApi.search(query, types, limit),
    });
}

export function useCreateMemory() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: memoryApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['memories'] });
        },
    });
}

export function useDeleteMemory() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: memoryApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['memories'] });
        },
    });
}

export function useMemoryStats() {
    return useQuery({
        queryKey: queryKeys.memoryStats,
        queryFn: memoryApi.stats,
        staleTime: 5 * 60 * 1000,
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Topics Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useTopicTree() {
    return useQuery({
        queryKey: queryKeys.topicTree,
        queryFn: topicsApi.tree,
        staleTime: 10 * 60 * 1000, // 10 min
    });
}

export function useTopicTrends() {
    return useQuery({
        queryKey: queryKeys.topicTrends,
        queryFn: topicsApi.trends,
        staleTime: 5 * 60 * 1000,
    });
}

export function useTopicActivity(topicId: string) {
    return useQuery({
        queryKey: queryKeys.topicActivity(topicId),
        queryFn: () => topicsApi.activity(topicId),
        staleTime: 5 * 60 * 1000,
        enabled: !!topicId,
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Graph Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useGraph(params: GraphParams = {}) {
    return useQuery({
        queryKey: queryKeys.graph(params),
        queryFn: () => graphApi.get(params),
        staleTime: 5 * 60 * 1000,
    });
}

export function useGraphNeighbors(nodeId: string, depth = 1) {
    return useQuery({
        queryKey: ['graph', 'neighbors', nodeId, depth],
        queryFn: () => graphApi.getNeighbors(nodeId, depth),
        enabled: !!nodeId,
    });
}

export function useGraphStats() {
    return useQuery({
        queryKey: queryKeys.graphStats,
        queryFn: graphApi.stats,
        staleTime: 5 * 60 * 1000,
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Analytics Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useAnomalies(status = 'new') {
    return useQuery({
        queryKey: queryKeys.anomalies(status),
        queryFn: () => analyticsApi.getAnomalies(status),
        staleTime: 1 * 60 * 1000, // 1 min - more frequent refresh
        refetchInterval: 5 * 60 * 1000, // Poll every 5 min
    });
}

export function useAcknowledgeAnomaly() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: analyticsApi.acknowledgeAnomaly,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['anomalies'] });
        },
    });
}

export function useResolveAnomaly() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, note }: { id: string; note?: string }) =>
            analyticsApi.resolveAnomaly(id, note),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['anomalies'] });
        },
    });
}

export function useDismissAnomaly() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: analyticsApi.dismissAnomaly,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['anomalies'] });
        },
    });
}

export function useCognitiveHealth() {
    return useQuery({
        queryKey: queryKeys.cognitiveHealth,
        queryFn: analyticsApi.getHealth,
        staleTime: 5 * 60 * 1000,
    });
}

export function useAnomalyStats() {
    return useQuery({
        queryKey: queryKeys.anomalyStats,
        queryFn: analyticsApi.anomalyStats,
        staleTime: 1 * 60 * 1000,
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Decisions Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useDecisions(limit = 20) {
    return useQuery({
        queryKey: queryKeys.decisions,
        queryFn: () => decisionsApi.list(limit),
        staleTime: 5 * 60 * 1000,
    });
}

export function useDecisionAnalysis(decisionId: string) {
    return useQuery({
        queryKey: queryKeys.decisionAnalysis(decisionId),
        queryFn: () => decisionsApi.getAnalysis(decisionId),
        staleTime: 10 * 60 * 1000,
        enabled: !!decisionId,
    });
}

export function useAnalyzeDecision() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: decisionsApi.analyze,
        onSuccess: (_, decisionId) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.decisionAnalysis(decisionId) });
        },
    });
}

export function useDecisionStats() {
    return useQuery({
        queryKey: queryKeys.decisionStats,
        queryFn: decisionsApi.stats,
        staleTime: 5 * 60 * 1000,
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Health Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useSystemHealth() {
    return useQuery({
        queryKey: queryKeys.systemHealth,
        queryFn: healthApi.system,
        staleTime: 30 * 1000, // 30 sec
        refetchInterval: 60 * 1000, // Poll every minute
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Messages Hooks
// ═══════════════════════════════════════════════════════════════════════════

export function useSendMessage() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ content, sessionId, mode }: { content: string; sessionId?: string; mode?: string }) =>
            messagesApi.send(content, sessionId, mode),
        onSuccess: (data) => {
            if (data.session_id) {
                queryClient.invalidateQueries({ queryKey: queryKeys.sessionHistory(data.session_id) });
            }
            // If memory was saved, refresh memories
            if (data.memory_saved) {
                queryClient.invalidateQueries({ queryKey: ['memories'] });
            }
        },
    });
}

export function useSessionHistory(sessionId: string) {
    return useQuery({
        queryKey: queryKeys.sessionHistory(sessionId),
        queryFn: () => messagesApi.getHistory(sessionId),
        staleTime: 30 * 1000,
        enabled: !!sessionId,
    });
}

export function useSessions() {
    return useQuery({
        queryKey: queryKeys.sessions,
        queryFn: () => messagesApi.listSessions(),
        staleTime: 5 * 60 * 1000,
    });
}
