/**
 * Digital Den — Trend Chart (Recharts)
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

interface TrendDataPoint {
    date: string;
    [key: string]: string | number;
}

interface TrendLine {
    key: string;
    name: string;
    color: string;
}

interface TrendChartProps {
    data: TrendDataPoint[];
    lines: TrendLine[];
    height?: number;
    onPointClick?: (data: TrendDataPoint) => void;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload) return null;

    return (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 shadow-lg">
            <p className="text-sm font-medium mb-1">{label}</p>
            {payload.map((entry: any, index: number) => (
                <p key={index} className="text-xs" style={{ color: entry.color }}>
                    {entry.name}: {entry.value}
                </p>
            ))}
        </div>
    );
};

export default function TrendChart({
    data,
    lines,
    height = 300,
    onPointClick
}: TrendChartProps) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <LineChart
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                onClick={(e: any) => {
                    if (e?.activePayload?.[0]?.payload) {
                        onPointClick?.(e.activePayload[0].payload);
                    }
                }}
            >
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis
                    dataKey="date"
                    stroke="#71717a"
                    tick={{ fill: '#71717a', fontSize: 12 }}
                />
                <YAxis
                    stroke="#71717a"
                    tick={{ fill: '#71717a', fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                    wrapperStyle={{ paddingTop: 10 }}
                    formatter={(value) => <span className="text-zinc-400">{value}</span>}
                />
                {lines.map((line) => (
                    <Line
                        key={line.key}
                        type="monotone"
                        dataKey={line.key}
                        name={line.name}
                        stroke={line.color}
                        strokeWidth={2}
                        dot={{ fill: line.color, strokeWidth: 0, r: 3 }}
                        activeDot={{ r: 6, strokeWidth: 2, stroke: '#fff' }}
                    />
                ))}
            </LineChart>
        </ResponsiveContainer>
    );
}

// Pre-configured Topic Trend Chart
export function TopicTrendChart({ data }: { data: TrendDataPoint[] }) {
    const defaultLines: TrendLine[] = [
        { key: 'finance', name: 'Финансы', color: '#3b82f6' },
        { key: 'hr', name: 'HR', color: '#22c55e' },
        { key: 'strategy', name: 'Стратегия', color: '#a855f7' },
    ];

    return <TrendChart data={data} lines={defaultLines} />;
}
