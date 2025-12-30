/**
 * Digital Denis — Zustand Store
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Global state management for Digital Denis frontend.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MemoryItem, Topic, GraphData, Anomaly, CognitiveHealth } from './api';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface MemoryFilters {
    item_type?: string;
    topic_id?: string;
    status?: string;
    limit: number;
    offset: number;
}

export interface GraphFilters {
    topic_id?: string;
    days: number;
    max_nodes: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Session Store
// ═══════════════════════════════════════════════════════════════════════════

interface SessionState {
    sessionId: string | null;
    isLoading: boolean;
    error: string | null;

    setSessionId: (id: string | null) => void;
    setLoading: (loading: boolean) => void;
    setIsLoading: (loading: boolean) => void; // alias for setLoading
    setError: (error: string | null) => void;
    clearSession: () => void;
}

export const useSessionStore = create<SessionState>()(
    persist(
        (set) => ({
            sessionId: null,
            isLoading: false,
            error: null,

            setSessionId: (id) => set({ sessionId: id }),
            setLoading: (loading) => set({ isLoading: loading }),
            setIsLoading: (loading) => set({ isLoading: loading }),
            setError: (error) => set({ error }),
            clearSession: () => set({ sessionId: null, error: null }),
        }),
        {
            name: 'dd-session',
            partialize: (state) => ({ sessionId: state.sessionId }),
        }
    )
);

// ═══════════════════════════════════════════════════════════════════════════
// Memory Store
// ═══════════════════════════════════════════════════════════════════════════

interface MemoryState {
    memories: MemoryItem[];
    total: number;
    filters: MemoryFilters;
    selectedMemory: MemoryItem | null;
    isLoading: boolean;

    setMemories: (memories: MemoryItem[], total: number) => void;
    setFilters: (filters: Partial<MemoryFilters>) => void;
    setSelectedMemory: (memory: MemoryItem | null) => void;
    setLoading: (loading: boolean) => void;
    clearFilters: () => void;
}

const defaultMemoryFilters: MemoryFilters = {
    limit: 20,
    offset: 0,
};

export const useMemoryStore = create<MemoryState>((set) => ({
    memories: [],
    total: 0,
    filters: defaultMemoryFilters,
    selectedMemory: null,
    isLoading: false,

    setMemories: (memories, total) => set({ memories, total }),
    setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters, offset: 0 }
    })),
    setSelectedMemory: (memory) => set({ selectedMemory: memory }),
    setLoading: (loading) => set({ isLoading: loading }),
    clearFilters: () => set({ filters: defaultMemoryFilters }),
}));

// ═══════════════════════════════════════════════════════════════════════════
// Topics Store
// ═══════════════════════════════════════════════════════════════════════════

interface TopicsState {
    topicTree: Topic[];
    activeTopic: Topic | null;
    expandedTopics: Set<string>;
    isLoading: boolean;

    setTopicTree: (tree: Topic[]) => void;
    setActiveTopic: (topic: Topic | null) => void;
    toggleExpanded: (topicId: string) => void;
    setLoading: (loading: boolean) => void;
}

export const useTopicsStore = create<TopicsState>((set) => ({
    topicTree: [],
    activeTopic: null,
    expandedTopics: new Set(),
    isLoading: false,

    setTopicTree: (tree) => set({ topicTree: tree }),
    setActiveTopic: (topic) => set({ activeTopic: topic }),
    toggleExpanded: (topicId) => set((state) => {
        const newExpanded = new Set(state.expandedTopics);
        if (newExpanded.has(topicId)) {
            newExpanded.delete(topicId);
        } else {
            newExpanded.add(topicId);
        }
        return { expandedTopics: newExpanded };
    }),
    setLoading: (loading) => set({ isLoading: loading }),
}));

// ═══════════════════════════════════════════════════════════════════════════
// Graph Store
// ═══════════════════════════════════════════════════════════════════════════

interface GraphState {
    graphData: GraphData | null;
    selectedNode: string | null;
    filters: GraphFilters;
    isLoading: boolean;

    setGraphData: (data: GraphData | null) => void;
    setSelectedNode: (nodeId: string | null) => void;
    setFilters: (filters: Partial<GraphFilters>) => void;
    setLoading: (loading: boolean) => void;
}

const defaultGraphFilters: GraphFilters = {
    days: 30,
    max_nodes: 100,
};

export const useGraphStore = create<GraphState>((set) => ({
    graphData: null,
    selectedNode: null,
    filters: defaultGraphFilters,
    isLoading: false,

    setGraphData: (data) => set({ graphData: data }),
    setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),
    setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters }
    })),
    setLoading: (loading) => set({ isLoading: loading }),
}));

// ═══════════════════════════════════════════════════════════════════════════
// Analytics Store
// ═══════════════════════════════════════════════════════════════════════════

interface AnalyticsState {
    anomalies: Anomaly[];
    unreadCount: number;
    cognitiveHealth: CognitiveHealth | null;
    isLoadingAnomalies: boolean;
    isLoadingHealth: boolean;

    setAnomalies: (anomalies: Anomaly[]) => void;
    removeAnomaly: (id: string) => void;
    setUnreadCount: (count: number) => void;
    setCognitiveHealth: (health: CognitiveHealth) => void;
    setLoadingAnomalies: (loading: boolean) => void;
    setLoadingHealth: (loading: boolean) => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
    anomalies: [],
    unreadCount: 0,
    cognitiveHealth: null,
    isLoadingAnomalies: false,
    isLoadingHealth: false,

    setAnomalies: (anomalies) => set({
        anomalies,
        unreadCount: anomalies.filter(a => a.status === 'new').length
    }),
    removeAnomaly: (id) => set((state) => ({
        anomalies: state.anomalies.filter(a => a.id !== id),
        unreadCount: state.anomalies.filter(a => a.id !== id && a.status === 'new').length,
    })),
    setUnreadCount: (count) => set({ unreadCount: count }),
    setCognitiveHealth: (health) => set({ cognitiveHealth: health }),
    setLoadingAnomalies: (loading) => set({ isLoadingAnomalies: loading }),
    setLoadingHealth: (loading) => set({ isLoadingHealth: loading }),
}));

// ═══════════════════════════════════════════════════════════════════════════
// UI Store
// ═══════════════════════════════════════════════════════════════════════════

interface UIState {
    sidebarOpen: boolean;
    theme: 'light' | 'dark' | 'system';
    commandPaletteOpen: boolean;

    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;
    setTheme: (theme: 'light' | 'dark' | 'system') => void;
    toggleCommandPalette: () => void;
}

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            sidebarOpen: true,
            theme: 'dark',
            commandPaletteOpen: false,

            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
            setSidebarOpen: (open) => set({ sidebarOpen: open }),
            setTheme: (theme) => set({ theme }),
            toggleCommandPalette: () => set((state) => ({
                commandPaletteOpen: !state.commandPaletteOpen
            })),
        }),
        {
            name: 'dd-ui',
            partialize: (state) => ({ theme: state.theme, sidebarOpen: state.sidebarOpen }),
        }
    )
);

// ═══════════════════════════════════════════════════════════════════════════
// Legacy compatibility export
// ═══════════════════════════════════════════════════════════════════════════

export const useAppStore = useSessionStore;
