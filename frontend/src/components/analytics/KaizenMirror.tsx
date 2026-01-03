/**
 * Digital Den — Kaizen Mirror Component
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Displays reflective observations in neutral language.
 * 
 * Key principles:
 * - No imperatives
 * - No recommendations
 * - Pure reflection
 * 
 * Based on: docs/kaizen_UI.md
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import client from '@/lib/api';

interface MirrorResponse {
    observations: string[];
}

export default function KaizenMirror() {
    const { data, isLoading, error } = useQuery<MirrorResponse>({
        queryKey: ['kaizen', 'mirror'],
        queryFn: async () => {
            const res = await client.get<MirrorResponse>('/kaizen/mirror?limit=3');
            return res.data;
        },
        staleTime: 60 * 1000, // 1 minute
    });

    if (isLoading) {
        return (
            <div className="bg-zinc-900 rounded-xl p-6 animate-pulse">
                <div className="h-6 bg-zinc-800 rounded w-1/3 mb-4"></div>
                <div className="space-y-2">
                    <div className="h-4 bg-zinc-800 rounded"></div>
                    <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return null; // Silently fail for optional component
    }

    return (
        <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
            <h2 className="text-lg font-semibold mb-4">💡 Kaizen-зеркало</h2>

            <div className="space-y-3">
                {data.observations.map((observation, index) => (
                    <div
                        key={index}
                        className="text-sm text-zinc-300 pl-3 border-l-2 border-zinc-700"
                    >
                        {observation}
                    </div>
                ))}
            </div>

            <p className="text-xs text-zinc-600 mt-4">
                Без оценок. Только отражение.
            </p>
        </div>
    );
}
