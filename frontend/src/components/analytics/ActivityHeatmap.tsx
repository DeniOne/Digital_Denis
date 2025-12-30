/**
 * Digital Denis — Activity Heatmap (D3.js)
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useMemo } from 'react';
import * as d3 from 'd3';

interface HeatmapCell {
    date: string;
    value: number;
    weekday: number;
    week: number;
}

interface ActivityHeatmapProps {
    data: HeatmapCell[];
    cellSize?: number;
    gap?: number;
    weeks?: number;
}

// Color scale like GitHub contribution graph
const colorScale = d3.scaleQuantize<string>()
    .domain([0, 10])
    .range(['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']);

export default function ActivityHeatmap({
    data,
    cellSize = 14,
    gap = 3,
    weeks = 12
}: ActivityHeatmapProps) {
    const width = 7 * (cellSize + gap);
    const height = weeks * (cellSize + gap);

    const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

    return (
        <div className="flex gap-2">
            {/* Day labels */}
            <div className="flex flex-col justify-around text-xs text-zinc-500 py-1">
                {days.map((day, i) => (
                    <span key={i} className="h-3 leading-3">{day}</span>
                ))}
            </div>

            {/* Heatmap grid */}
            <div>
                <svg width={height} height={width}>
                    <g transform="rotate(90) translate(0, -1)">
                        {data.map((cell, i) => {
                            const x = cell.weekday * (cellSize + gap);
                            const y = cell.week * (cellSize + gap);

                            return (
                                <rect
                                    key={i}
                                    x={x}
                                    y={y}
                                    width={cellSize}
                                    height={cellSize}
                                    rx={3}
                                    fill={colorScale(cell.value)}
                                    className="transition-opacity hover:opacity-80"
                                >
                                    <title>{`${cell.date}: ${cell.value} записей`}</title>
                                </rect>
                            );
                        })}
                    </g>
                </svg>

                {/* Legend */}
                <div className="flex items-center gap-2 mt-3 text-xs text-zinc-500">
                    <span>Less</span>
                    {colorScale.range().map((color, i) => (
                        <span
                            key={i}
                            className="w-3 h-3 rounded-sm"
                            style={{ backgroundColor: color }}
                        />
                    ))}
                    <span>More</span>
                </div>
            </div>
        </div>
    );
}

// Simple seeded random for deterministic results (SSR-compatible)
function seededRandom(seed: number): number {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
}

// Generate sample heatmap data (deterministic for SSR)
export function generateHeatmapData(weeks: number = 12): HeatmapCell[] {
    const data: HeatmapCell[] = [];
    // Use a fixed base date for deterministic data
    const baseDate = new Date('2025-12-30');

    for (let w = 0; w < weeks; w++) {
        for (let d = 0; d < 7; d++) {
            const date = new Date(baseDate);
            date.setDate(date.getDate() - (weeks - w - 1) * 7 - (6 - d));

            // Deterministic "random" based on position
            const seed = w * 7 + d + 1;
            const value = Math.floor(seededRandom(seed) * 12);

            data.push({
                date: date.toISOString().split('T')[0],
                value,
                weekday: d,
                week: w,
            });
        }
    }

    return data;
}
