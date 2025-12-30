'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface TopicsChartProps {
    topics: { id: string; name: string; count: number }[];
}

export function TopicsChart({ topics }: TopicsChartProps) {
    if (!topics || topics.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-gray-500 italic">
                Недостаточно данных для визуализации тем
            </div>
        );
    }

    const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#6366f1'];

    return (
        <div className="h-[350px] w-full">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-1.5 h-6 bg-blue-500 rounded-full"></span>
                Распределение топиков
            </h3>
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={topics}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="count"
                        nameKey="name"
                        stroke="none"
                    >
                        {topics.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#111827',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '12px',
                            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                        }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend
                        verticalAlign="bottom"
                        align="center"
                        wrapperStyle={{ paddingTop: '20px' }}
                        formatter={(value) => <span className="text-xs text-gray-400 pr-2">{value}</span>}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
