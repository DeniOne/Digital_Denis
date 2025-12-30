/**
 * Digital Denis — Cognitive Health Page
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useAnomalies, useCognitiveHealth, useAcknowledgeAnomaly, useDismissAnomaly } from '@/lib/hooks';
import ActivityHeatmap, { generateHeatmapData } from '@/components/analytics/ActivityHeatmap';
import type { Anomaly } from '@/lib/api';

function SeverityBadge({ severity }: { severity: string }) {
    const colors: Record<string, string> = {
        low: 'bg-green-500/20 text-green-400',
        medium: 'bg-yellow-500/20 text-yellow-400',
        high: 'bg-orange-500/20 text-orange-400',
        critical: 'bg-red-500/20 text-red-400',
    };

    return (
        <span className={`px-2 py-1 rounded text-xs font-medium ${colors[severity] || colors.medium}`}>
            {severity.toUpperCase()}
        </span>
    );
}

function HealthScore({ score, label }: { score: number; label: string }) {
    const getColor = (s: number) => {
        if (s >= 0.8) return 'text-green-400';
        if (s >= 0.6) return 'text-yellow-400';
        return 'text-red-400';
    };

    return (
        <div className="text-center">
            <div className={`text-3xl font-bold ${getColor(score)}`}>
                {(score * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-zinc-400">{label}</div>
        </div>
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
                <span>{new Date(anomaly.detected_at).toLocaleDateString()}</span>
            </div>

            {anomaly.status === 'new' && (
                <div className="flex gap-2">
                    <button
                        onClick={() => acknowledge.mutate(anomaly.id)}
                        className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-sm hover:bg-blue-500/30"
                        disabled={acknowledge.isPending}
                    >
                        ✓ Принять
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
            <h1 className="text-2xl font-bold mb-6">💚 Когнитивное здоровье</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Health Overview */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Overall Health Card */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Общий обзор</h2>

                        {healthLoading ? (
                            <div className="text-zinc-500">Загрузка...</div>
                        ) : health ? (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                <HealthScore score={health.overall_score} label="Общий" />
                                <HealthScore score={health.decision_quality} label="Решения" />
                                <HealthScore score={health.memory_diversity} label="Разнообразие" />
                                <HealthScore score={health.thinking_consistency} label="Системность" />
                            </div>
                        ) : null}
                    </div>

                    {/* Quick Stats */}
                    {health && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-blue-400">{health.total_memories}</div>
                                <div className="text-sm text-zinc-400">Память</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-green-400">{health.active_topics}</div>
                                <div className="text-sm text-zinc-400">Темы</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-yellow-400">{health.anomalies_count}</div>
                                <div className="text-sm text-zinc-400">Аномалии</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-sm text-zinc-400">Активность</div>
                                <div className="text-xs text-zinc-500">
                                    {health.last_activity ? new Date(health.last_activity).toLocaleDateString() : 'Н/Д'}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Activity Heatmap */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Активность (90д)</h2>
                        <div className="flex justify-center">
                            <ActivityHeatmap data={generateHeatmapData(12)} weeks={12} />
                        </div>
                    </div>

                    {/* Anomalies List */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold">⚠️ Активные аномалии</h2>
                            <span className="text-sm text-zinc-500">
                                {anomalies?.length || 0} непрочитано
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
                                ✅ Аномалий не обнаружено
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Tips */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-3">💡 Советы</h2>
                        <div className="text-sm text-zinc-400 space-y-3">
                            <p>• Регулярно проверяйте аномалии для отслеживания паттернов мышления</p>
                            <p>• Разнообразьте темы сообщений для когнитивного баланса</p>
                            <p>• Высокое качество решений указывает на четкую аргументацию</p>
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-3">Легенда важности</h2>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-green-400" />
                                <span className="text-sm">Низкая — небольшой сдвиг</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-yellow-400" />
                                <span className="text-sm">Средняя — заметное изменение</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-orange-400" />
                                <span className="text-sm">Высокая — требует внимания</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-red-400" />
                                <span className="text-sm">Критическая — срочное действие</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

