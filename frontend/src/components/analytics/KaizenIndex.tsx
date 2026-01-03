/**
 * Digital Den — Kaizen Index Component
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Displays the Kaizen Index with relative dynamics across multiple time periods.
 * Includes expandable section for long-term periods (quarter, half-year, year).
 * 
 * Based on: docs/kaizen_UI.md
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import client, { type KaizenIndex } from '@/lib/api';

// State labels with emoji
const STATE_LABELS: Record<string, { label: string; emoji: string; color: string }> = {
    growth: {
        label: 'Рост',
        emoji: '📈',
        color: 'text-green-400',
    },
    plateau: {
        label: 'Стабилизация',
        emoji: '➖',
        color: 'text-zinc-400',
    },
    fluctuation: {
        label: 'Флуктуации',
        emoji: '⚠️',
        color: 'text-yellow-400',
    },
    overload: {
        label: 'Перегруз',
        emoji: '🔴',
        color: 'text-red-400',
    },
};

// Extended periods for the expandable section
interface ExtendedPeriods {
    quarter: number | null;
    half_year: number | null;
    year: number | null;
    all_time: number | null;
}

function formatChange(value: number | null | undefined): { text: string; color: string } {
    if (value === null || value === undefined) {
        return { text: '—', color: 'text-zinc-500' };
    }
    if (value > 0) {
        return { text: `+${value.toFixed(1)}%`, color: 'text-green-400' };
    } else if (value < 0) {
        return { text: `${value.toFixed(1)}%`, color: 'text-red-400' };
    }
    return { text: '0%', color: 'text-zinc-400' };
}

export default function KaizenIndexCard() {
    const [showExtended, setShowExtended] = useState(false);

    const { data, isLoading, error } = useQuery<KaizenIndex & { extended?: ExtendedPeriods }>({
        queryKey: ['kaizen', 'index'],
        queryFn: async () => {
            const res = await client.get<KaizenIndex>('/kaizen/index');
            return res.data;
        },
        staleTime: 30 * 1000, // 30 seconds
    });

    if (isLoading) {
        return (
            <div className="bg-zinc-900 rounded-xl p-6 animate-pulse">
                <div className="h-6 bg-zinc-800 rounded w-1/3 mb-4"></div>
                <div className="h-12 bg-zinc-800 rounded w-1/2"></div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-zinc-900 rounded-xl p-6">
                <div className="text-zinc-500">Не удалось загрузить Kaizen-индекс</div>
            </div>
        );
    }

    const stateInfo = STATE_LABELS[data.user_state] || STATE_LABELS.plateau;
    const change14d = formatChange(data.change_14d);
    const change7d = formatChange(data.change_7d);
    const change30d = formatChange(data.change_30d);

    // Extended periods (will be available from API in future)
    const extended = (data as any).extended || {};
    const changeQuarter = formatChange(extended.quarter);
    const changeHalfYear = formatChange(extended.half_year);
    const changeYear = formatChange(extended.year);
    const changeAllTime = formatChange(extended.all_time);

    return (
        <div className="bg-zinc-900 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">🔄 Kaizen-индекс</h2>

            {/* Main Index Display */}
            <div className="flex items-center gap-4 mb-6">
                <div className={`text-4xl font-bold ${change14d.color}`}>
                    {change14d.text}
                </div>
                <div className="text-sm text-zinc-400">
                    за 14 дней
                </div>
            </div>

            {/* Period Changes - Default */}
            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-zinc-800 rounded-lg p-3">
                    <div className={`text-xl font-semibold ${change7d.color}`}>
                        {change7d.text}
                    </div>
                    <div className="text-xs text-zinc-500">за 7 дней</div>
                </div>
                <div className="bg-zinc-800 rounded-lg p-3">
                    <div className={`text-xl font-semibold ${change30d.color}`}>
                        {change30d.text}
                    </div>
                    <div className="text-xs text-zinc-500">за 30 дней</div>
                </div>
            </div>

            {/* Toggle Extended Periods */}
            <button
                onClick={() => setShowExtended(!showExtended)}
                className="w-full flex items-center justify-center gap-2 text-sm text-zinc-400 hover:text-zinc-300 py-2 transition-colors"
            >
                <span>📊</span>
                <span>{showExtended ? 'Скрыть периоды' : 'Показать больше периодов'}</span>
                <span className={`transition-transform ${showExtended ? 'rotate-180' : ''}`}>▾</span>
            </button>

            {/* Extended Periods - Expandable */}
            {showExtended && (
                <div className="mt-4 bg-zinc-800/50 rounded-lg p-4 space-y-3 animate-in slide-in-from-top-2">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-zinc-400">Квартал (90д)</span>
                        <span className={`font-semibold ${changeQuarter.color}`}>
                            {changeQuarter.text}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-zinc-400">Полгода (180д)</span>
                        <span className={`font-semibold ${changeHalfYear.color}`}>
                            {changeHalfYear.text}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-zinc-400">Год (365д)</span>
                        <span className={`font-semibold ${changeYear.color}`}>
                            {changeYear.text}
                        </span>
                    </div>
                    <div className="flex justify-between items-center border-t border-zinc-700 pt-3">
                        <span className="text-sm text-zinc-400">Всё время</span>
                        <span className={`font-semibold ${changeAllTime.color}`}>
                            {changeAllTime.text}
                        </span>
                    </div>
                </div>
            )}

            {/* State Badge */}
            <div className="flex items-center gap-2 mt-4">
                <span className="text-base">{stateInfo.emoji}</span>
                <span className={`font-medium ${stateInfo.color}`}>
                    Состояние: {stateInfo.label}
                </span>
            </div>

            {/* Note about comparison */}
            <p className="text-xs text-zinc-600 mt-4 border-t border-zinc-800 pt-3">
                💡 Сравнение только с собой: ты сегодня ↔ ты вчера
            </p>
        </div>
    );
}
