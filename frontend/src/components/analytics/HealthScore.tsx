/**
 * Digital Den — Health Score Gauge (Recharts)
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import {
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
    ResponsiveContainer,
} from 'recharts';

interface HealthScoreProps {
    score: number;
    label?: string;
    size?: number;
}

function getColor(score: number): string {
    if (score >= 80) return '#22c55e'; // green
    if (score >= 60) return '#eab308'; // yellow
    if (score >= 40) return '#f97316'; // orange
    return '#ef4444'; // red
}

function getLabel(score: number): string {
    if (score >= 80) return 'Отлично';
    if (score >= 60) return 'Хорошо';
    if (score >= 40) return 'Средне';
    return 'Нужно внимание';
}

export default function HealthScore({ score, label, size = 200 }: HealthScoreProps) {
    const color = getColor(score);
    const statusLabel = label || getLabel(score);

    const data = [
        {
            value: score,
            fill: color,
        },
    ];

    return (
        <div className="relative" style={{ width: size, height: size }}>
            <ResponsiveContainer>
                <RadialBarChart
                    innerRadius="70%"
                    outerRadius="100%"
                    data={data}
                    startAngle={180}
                    endAngle={0}
                >
                    <PolarAngleAxis
                        type="number"
                        domain={[0, 100]}
                        angleAxisId={0}
                        tick={false}
                    />
                    <RadialBar
                        dataKey="value"
                        cornerRadius={10}
                        background={{ fill: '#27272a' }}
                    />
                </RadialBarChart>
            </ResponsiveContainer>

            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span
                    className="text-3xl font-bold"
                    style={{ color }}
                >
                    {score}%
                </span>
                <span className="text-xs text-zinc-400 mt-1">{statusLabel}</span>
            </div>
        </div>
    );
}

// Mini version for dashboards
export function HealthScoreMini({ score, label }: { score: number; label: string }) {
    const color = getColor(score);

    return (
        <div className="flex items-center gap-3">
            <div
                className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold"
                style={{
                    backgroundColor: `${color}20`,
                    color,
                }}
            >
                {score}
            </div>
            <div>
                <div className="font-medium">{label}</div>
                <div className="text-xs text-zinc-400">{getLabel(score)}</div>
            </div>
        </div>
    );
}
