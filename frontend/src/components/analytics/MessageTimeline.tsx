'use client';

import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MessageTimelineProps {
    data: { date: string; count: number }[];
}

export function MessageTimeline({ data }: MessageTimelineProps) {
    if (!data || data.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-gray-500 italic">
                Нет данных об активности за этот период
            </div>
        );
    }

    // Format dates for display
    const chartData = data.map(d => ({
        ...d,
        formattedDate: new Date(d.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    }));

    return (
        <div className="h-[350px] w-full">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-1.5 h-6 bg-purple-500 rounded-full"></span>
                Объем записей (Timeline)
            </h3>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                        dataKey="formattedDate"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 10 }}
                        minTickGap={30}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 10 }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#111827',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '12px',
                            padding: '10px'
                        }}
                        labelStyle={{ color: '#fff', marginBottom: '4px', fontWeight: 'bold' }}
                        itemStyle={{ color: '#8b5cf6' }}
                        labelFormatter={(label) => `Дата: ${label}`}
                    />
                    <Area
                        type="monotone"
                        dataKey="count"
                        stroke="#8b5cf6"
                        strokeWidth={3}
                        fillOpacity={1}
                        fill="url(#colorCount)"
                        animationDuration={1500}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
