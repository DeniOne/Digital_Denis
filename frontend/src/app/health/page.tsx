/**
 * Digital Denis — Cognitive Health Page
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useAnomalies, useCognitiveHealth, useAcknowledgeAnomaly, useDismissAnomaly } from '@/lib/hooks';
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
                    <span>Change: {anomaly.deviation_percent > 0 ? '+' : ''}{anomaly.deviation_percent.toFixed(0)}%</span>
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
                        ✓ Acknowledge
                    </button>
                    <button
                        onClick={() => dismiss.mutate(anomaly.id)}
                        className="px-3 py-1 bg-zinc-700 text-zinc-300 rounded text-sm hover:bg-zinc-600"
                        disabled={dismiss.isPending}
                    >
                        ✕ Dismiss
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
            <h1 className="text-2xl font-bold mb-6">💚 Cognitive Health</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Health Overview */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Overall Health Card */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Health Overview</h2>

                        {healthLoading ? (
                            <div className="text-zinc-500">Loading...</div>
                        ) : health ? (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                <HealthScore score={health.overall_score} label="Overall" />
                                <HealthScore score={health.decision_quality} label="Decisions" />
                                <HealthScore score={health.memory_diversity} label="Diversity" />
                                <HealthScore score={health.thinking_consistency} label="Consistency" />
                            </div>
                        ) : null}
                    </div>

                    {/* Quick Stats */}
                    {health && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-blue-400">{health.total_memories}</div>
                                <div className="text-sm text-zinc-400">Memories</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-green-400">{health.active_topics}</div>
                                <div className="text-sm text-zinc-400">Topics</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-2xl font-bold text-yellow-400">{health.anomalies_count}</div>
                                <div className="text-sm text-zinc-400">Anomalies</div>
                            </div>
                            <div className="bg-zinc-900 rounded-xl p-4 text-center">
                                <div className="text-sm text-zinc-400">Last Active</div>
                                <div className="text-xs text-zinc-500">
                                    {health.last_activity ? new Date(health.last_activity).toLocaleDateString() : 'N/A'}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Anomalies List */}
                    <div className="bg-zinc-900 rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold">⚠️ Active Anomalies</h2>
                            <span className="text-sm text-zinc-500">
                                {anomalies?.length || 0} unread
                            </span>
                        </div>

                        {anomaliesLoading ? (
                            <div className="text-zinc-500">Loading...</div>
                        ) : anomalies && anomalies.length > 0 ? (
                            <div className="space-y-4">
                                {anomalies.map((anomaly: Anomaly) => (
                                    <AnomalyCard key={anomaly.id} anomaly={anomaly} />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-zinc-500 py-8">
                                ✅ No active anomalies
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Tips */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-3">💡 Tips</h2>
                        <div className="text-sm text-zinc-400 space-y-3">
                            <p>• Review anomalies regularly to track thinking patterns</p>
                            <p>• Diversify topics to improve cognitive balance</p>
                            <p>• High decision quality indicates clear reasoning</p>
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-3">Severity Legend</h2>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-green-400" />
                                <span className="text-sm">Low — minor pattern shift</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-yellow-400" />
                                <span className="text-sm">Medium — notable change</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-orange-400" />
                                <span className="text-sm">High — requires attention</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-red-400" />
                                <span className="text-sm">Critical — action needed</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
