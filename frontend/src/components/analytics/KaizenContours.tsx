/**
 * Digital Den — Kaizen Contours Component
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Displays the 4 Kaizen contours with trends and changes.
 * 
 * Based on: docs/kaizen_UI.md
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import client, { type KaizenContour } from '@/lib/api';

// Trend indicators
const TREND_ICONS: Record<string, { icon: string; color: string }> = {
    up: { icon: '▲', color: 'text-green-400' },
    down: { icon: '▼', color: 'text-red-400' },
    stable: { icon: '➖', color: 'text-zinc-400' },
    volatile: { icon: '⚠', color: 'text-yellow-400' },
};

interface ContourCardProps {
    contour: KaizenContour;
}

function ContourCard({ contour }: ContourCardProps) {
    const trend = TREND_ICONS[contour.trend] || TREND_ICONS.stable;

    // Format change percentage
    const changeText = contour.change_pct > 0
        ? `+${contour.change_pct.toFixed(1)}%`
        : `${contour.change_pct.toFixed(1)}%`;

    const changeColor = contour.change_pct > 0
        ? 'text-green-400'
        : contour.change_pct < 0
            ? 'text-red-400'
            : 'text-zinc-400';

    return (
        <div className="bg-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{contour.icon}</span>
                <h3 className="font-medium text-white">{contour.name}</h3>
            </div>

            <p className="text-sm text-zinc-400 mb-3">
                {contour.description}
            </p>

            <div className="flex items-center justify-between">
                {/* Trend with change */}
                <div className="flex items-center gap-2">
                    <span className={`text-lg ${trend.color}`}>{trend.icon}</span>
                    <span className={`text-sm font-medium ${changeColor}`}>
                        {changeText}
                    </span>
                </div>

                {/* Score indicator (subtle, not prominent) */}
                <div className="text-xs text-zinc-500">
                    {(contour.score * 100).toFixed(0)}
                </div>
            </div>
        </div>
    );
}

export default function KaizenContours() {
    const { data, isLoading, error } = useQuery<{ contours: KaizenContour[] }>({
        queryKey: ['kaizen', 'contours'],
        queryFn: async () => {
            const res = await client.get<{ contours: KaizenContour[] }>('/kaizen/contours');
            return res.data;
        },
        staleTime: 30 * 1000,
    });

    if (isLoading) {
        return (
            <div className="grid grid-cols-2 gap-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="bg-zinc-800 rounded-xl p-4 animate-pulse">
                        <div className="h-6 bg-zinc-700 rounded w-2/3 mb-2"></div>
                        <div className="h-4 bg-zinc-700 rounded w-full mb-3"></div>
                        <div className="h-4 bg-zinc-700 rounded w-1/3"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-zinc-900 rounded-xl p-6">
                <div className="text-zinc-500">Не удалось загрузить контуры Kaizen</div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold">🧭 Контуры Kaizen</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.contours.map(contour => (
                    <ContourCard key={contour.contour} contour={contour} />
                ))}
            </div>

            <p className="text-xs text-zinc-600">
                📌 Тренды показывают направление, а не оценку. Плато — нормально.
            </p>
        </div>
    );
}
