/**
 * Digital Den — Cognitive Health Page (Kaizen Edition)
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Refactored to focus on DYNAMICS, not status.
 * 
 * Key UX Principle:
 * User should think: "Я вижу, что со мной происходит"
 * NOT: "Я молодец / я плохой"
 * 
 * Based on: docs/kaizen_UI.md
 */

'use client';

import { useAnomalies, useCognitiveHealth, useAcknowledgeAnomaly, useDismissAnomaly } from '@/lib/hooks';
import ActivityHeatmap, { generateHeatmapData } from '@/components/analytics/ActivityHeatmap';
import KaizenIndexCard from '@/components/analytics/KaizenIndex';
import KaizenContours from '@/components/analytics/KaizenContours';
import KaizenMirror from '@/components/analytics/KaizenMirror';
import type { Anomaly } from '@/lib/api';

function SeverityBadge({ severity }: { severity: string }) {
    // Changed labels to be more neutral
    const colors: Record<string, string> = {
        low: 'bg-zinc-500/20 text-zinc-400',
        medium: 'bg-yellow-500/20 text-yellow-400',
        high: 'bg-orange-500/20 text-orange-400',
        critical: 'bg-red-500/20 text-red-400',
    };

    const labels: Record<string, string> = {
        low: 'Наблюдение',
        medium: 'Отмечено',
        high: 'Внимание',
        critical: 'Срочно',
    };

    return (
        <span className={`px-2 py-1 rounded text-xs font-medium ${colors[severity] || colors.medium}`}>
            {labels[severity] || severity.toUpperCase()}
        </span>
    );
}

function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
    const acknowledge = useAcknowledgeAnomaly();
    const dismiss = useDismissAnomaly();

    return (
        <div className="bg-zinc-800 rounded-xl p-4">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="font-medium">{anomaly.title}</h3>
                    <p className="text-sm text-zinc-400">{anomaly.anomaly_type}</p>
                </div>
                <SeverityBadge severity={anomaly.severity} />
            </div>

            {anomaly.interpretation && (
                <p className="text-sm text-zinc-300 mb-3">{anomaly.interpretation}</p>
            )}

            <div className="flex gap-4 text-xs text-zinc-500 mb-3">
                {anomaly.deviation_percent && (
                    <span>Изменение: {anomaly.deviation_percent > 0 ? '+' : ''}{anomaly.deviation_percent.toFixed(0)}%</span>
                )}
                <span>{new Date(anomaly.detected_at).toLocaleDateString('ru-RU')}</span>
            </div>

            {anomaly.status === 'new' && (
                <div className="flex gap-2">
                    <button
                        onClick={() => acknowledge.mutate(anomaly.id)}
                        className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-sm hover:bg-blue-500/30"
                        disabled={acknowledge.isPending}
                    >
                        ✓ Увидел
                    </button>
                    <button
                        onClick={() => dismiss.mutate(anomaly.id)}
                        className="px-3 py-1 bg-zinc-700 text-zinc-300 rounded text-sm hover:bg-zinc-600"
                        disabled={dismiss.isPending}
                    >
                        ✕ Скрыть
                    </button>
                </div>
            )}
        </div>
    );
}

export default function HealthPage() {
    const { data: health, isLoading: healthLoading } = useCognitiveHealth();
    const { data: anomalies, isLoading: anomaliesLoading } = useAnomalies('new');

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6">
            <h1 className="text-2xl font-bold mb-2">🔄 Когнитивная динамика</h1>
            <p className="text-zinc-400 text-sm mb-6">
                Наблюдение, а не оценка. Динамика, а не статус.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Kaizen Index Card */}
                    <KaizenIndexCard />

                    {/* Kaizen Contours */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <KaizenContours />
                    </div>

                    {/* Activity Heatmap */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">📊 Активность (90д)</h2>
                        <div className="flex justify-center">
                            <ActivityHeatmap data={generateHeatmapData(12)} weeks={12} />
                        </div>
                        <p className="text-xs text-zinc-600 mt-4 text-center">
                            Активность + качество: плотность мышления, не просто количество
                        </p>
                    </div>

                    {/* Anomalies / Fluctuations */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold">⚡ Флуктуации</h2>
                            <span className="text-sm text-zinc-500">
                                {anomalies?.length || 0} новых
                            </span>
                        </div>

                        {anomaliesLoading ? (
                            <div className="text-zinc-500">Загрузка...</div>
                        ) : anomalies && anomalies.length > 0 ? (
                            <div className="space-y-4">
                                {anomalies.map((anomaly: Anomaly) => (
                                    <AnomalyCard key={anomaly.id} anomaly={anomaly} />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-zinc-500 py-8">
                                ✅ Значимых отклонений не зафиксировано
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Kaizen Mirror */}
                    <KaizenMirror />

                    {/* Quick Stats (subtle, not prominent) */}
                    {health && (
                        <div className="bg-zinc-900 rounded-xl p-4">
                            <h2 className="text-sm font-medium text-zinc-400 mb-3">📈 Статистика</h2>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Память</span>
                                    <span className="text-zinc-300">{health.total_memories}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Темы</span>
                                    <span className="text-zinc-300">{health.active_topics}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Флуктуации</span>
                                    <span className="text-zinc-300">{health.anomalies_count}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Legend */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-sm font-medium text-zinc-400 mb-3">🧭 Тренды</h2>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="text-green-400">▲</span>
                                <span className="text-sm text-zinc-400">Рост — положительная динамика</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-zinc-400">➖</span>
                                <span className="text-sm text-zinc-400">Плато — стабильность (нормально)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-red-400">▼</span>
                                <span className="text-sm text-zinc-400">Снижение — сигнал для наблюдения</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-yellow-400">⚠</span>
                                <span className="text-sm text-zinc-400">Флуктуации — нестабильность</span>
                            </div>
                        </div>
                    </div>

                    {/* Philosophy Note */}
                    <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                        <p className="text-xs text-zinc-500 leading-relaxed">
                            💡 <strong>Философия Kaizen:</strong><br />
                            Ты развиваешься. ИИ наблюдает. Система запоминает.<br />
                            Ты видишь динамику — не вердикт.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
