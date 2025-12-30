'use client';

import React from 'react';
import {
    MessageSquare,
    Zap,
    CheckCircle,
    TrendingUp
} from 'lucide-react';

interface StatsCardsProps {
    summary: {
        total_memories: number;
        by_type: Record<string, number>;
        streak: number;
    };
}

export function StatsCards({ summary }: StatsCardsProps) {
    const cards = [
        {
            label: 'Всего записей',
            value: summary.total_memories,
            icon: <MessageSquare className="w-6 h-6" />,
            color: 'blue',
            description: 'Все активные воспоминания'
        },
        {
            label: 'Инсайты',
            value: summary.by_type['insight'] || 0,
            icon: <Zap className="w-6 h-6" />,
            color: 'amber',
            description: 'Важные открытия и идеи'
        },
        {
            label: 'Решения',
            value: summary.by_type['decision'] || 0,
            icon: <CheckCircle className="w-6 h-6" />,
            color: 'emerald',
            description: 'Принятые и зафиксированные'
        },
        {
            label: 'Серия (Streak)',
            value: summary.streak,
            icon: <TrendingUp className="w-6 h-6" />,
            color: 'rose',
            description: 'Дней активности подряд'
        }
    ];

    const getColorClasses = (color: string) => {
        const maps: Record<string, string> = {
            blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
            emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
        };
        return maps[color] || maps.blue;
    };

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {cards.map((card, i) => (
                <div
                    key={i}
                    className="group relative overflow-hidden bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6 transition-all hover:bg-gray-800/60 hover:border-white/10"
                >
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-gray-400 text-sm font-medium">{card.label}</p>
                            <h3 className="text-3xl font-bold mt-1 tracking-tight">{card.value}</h3>
                        </div>
                        <div className={`p-3 rounded-xl border ${getColorClasses(card.color)}`}>
                            {card.icon}
                        </div>
                    </div>
                    <p className="text-gray-500 text-xs mt-4">{card.description}</p>

                    {/* subtle glow effect */}
                    <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all"></div>
                </div>
            ))}
        </div>
    );
}
