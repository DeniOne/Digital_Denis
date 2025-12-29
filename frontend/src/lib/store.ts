import { create } from 'zustand';

interface AppState {
    sessionId: string | null;
    setSessionId: (id: string) => void;
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
    sessionId: null,
    setSessionId: (id) => set({ sessionId: id }),
    isLoading: false,
    setIsLoading: (loading) => set({ isLoading: loading }),
}));
