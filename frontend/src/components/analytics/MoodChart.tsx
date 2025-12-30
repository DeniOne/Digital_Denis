'use client';

import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';

interface MoodData {
    date: string;
    mood: number; // -1.0 to 1.0
    count: number;
}

interface MoodChartProps {
    data: MoodData[];
}

export function MoodChart({ data }: MoodChartProps) {
    // Determine gradient color based on average mood
    const avgMood = data.reduce((acc, curr) => acc + curr.mood, 0) / (data.length || 1);
    const strokeColor = avgMood >= 0 ? '#10b981' : '#f43f5e'; // Emerald or Rose

    return (
        <div className="w-full h-[300px]">
            {data.length === 0 ? (
                <div className="flex h-full items-center justify-center text-gray-500">
                    Нет данных о настроении за этот период
                </div>
            ) : (
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis
                            dataKey="date"
                            stroke="#9ca3af"
                            fontSize={12}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                        />
                        <YAxis
                            stroke="#9ca3af"
                            fontSize={12}
                            domain={[-1, 1]}
                            ticks={[-1, -0.5, 0, 0.5, 1]}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '0.5rem' }}
                            itemStyle={{ color: '#e5e7eb' }}
                            formatter={(value: number) => [value.toFixed(2), 'Настроение']}
                            labelFormatter={(label) => new Date(label).toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })}
                        />
                        <ReferenceLine y={0} stroke="#4b5563" strokeDasharray="3 3" />
                        <Line
                            type="monotone"
                            dataKey="mood"
                            stroke={strokeColor}
                            strokeWidth={2}
                            dot={{ fill: strokeColor, r: 4 }}
                            activeDot={{ r: 6, fill: '#fff' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}
