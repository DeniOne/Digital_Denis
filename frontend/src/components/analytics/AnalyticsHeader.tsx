'use client';

import React from 'react';

interface AnalyticsHeaderProps {
    period: number;
    setPeriod: (period: number) => void;
    title?: string;
}

export function AnalyticsHeader({ period, setPeriod, title = "Аналитика системы" }: AnalyticsHeaderProps) {
    const periods = [
        { label: '7 дней', value: 7 },
        { label: '30 дней', value: 30 },
        { label: '90 дней', value: 90 },
        { label: 'Год', value: 365 },
    ];

    return (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    {title}
                </h1>
                <p className="text-gray-400 mt-1">
                    Отслеживайте работу вашего цифрового сознания и когнитивные тренды.
                </p>
            </div>

            <div className="flex p-1 bg-gray-800/50 backdrop-blur-md rounded-xl border border-white/5 self-start md:self-center">
                {periods.map((p) => (
                    <button
                        key={p.value}
                        onClick={() => setPeriod(p.value)}
                        className={`
              px-4 py-2 text-sm font-medium rounded-lg transition-all
              ${period === p.value
                                ? 'bg-blue-600/20 text-blue-400 shadow-[0_0_15px_rgba(37,99,235,0.2)]'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'}
            `}
                    >
                        {p.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
