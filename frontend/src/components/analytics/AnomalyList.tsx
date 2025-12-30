'use client';

import React from 'react';
import { Anomaly } from '@/lib/api';
import { AlertTriangle, TrendingUp, TrendingDown, Brain, Zap, CheckCircle } from 'lucide-react';

interface AnomalyListProps {
    anomalies: Anomaly[];
}

export function AnomalyList({ anomalies }: AnomalyListProps) {
    const getIcon = (type: string) => {
        switch (type) {
            case 'topic_spike': return <TrendingUp className="w-5 h-5 text-emerald-400" />;
            case 'topic_drop': return <TrendingDown className="w-5 h-5 text-rose-400" />;
            case 'confidence_drop': return <AlertTriangle className="w-5 h-5 text-amber-400" />;
            case 'decision_surge': return <Zap className="w-5 h-5 text-blue-400" />;
            default: return <Brain className="w-5 h-5 text-purple-400" />;
        }
    };

    const getSeverityStyle = (severity: string) => {
        switch (severity) {
            case 'critical': return 'border-rose-500/50 bg-rose-500/10';
            case 'high': return 'border-orange-500/50 bg-orange-500/10';
            case 'medium': return 'border-amber-500/50 bg-amber-500/10';
            default: return 'border-blue-500/50 bg-blue-500/10';
        }
    };

    return (
        <div className="space-y-4">
            {anomalies.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-gray-500 border border-white/5 rounded-2xl bg-gray-900/20">
                    <CheckCircle className="w-8 h-8 mb-2 opacity-50" />
                    <p>Аномалий не обнаружено. Паттерны мышления стабильны.</p>
                </div>
            ) : (
                anomalies.map((anomaly) => (
                    <div
                        key={anomaly.id}
                        className={`p-4 rounded-2xl border backdrop-blur-sm transition-all hover:scale-[1.01] ${getSeverityStyle(anomaly.severity)}`}
                    >
                        <div className="flex items-start gap-3">
                            <div className="mt-1 p-2 bg-gray-900/30 rounded-full">
                                {getIcon(anomaly.anomaly_type)}
                            </div>
                            <div className="flex-1">
                                <div className="flex justify-between items-start">
                                    <h4 className="font-semibold text-gray-200">{anomaly.title}</h4>
                                    <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-gray-900/40 text-gray-400 border border-white/5">
                                        {new Date(anomaly.detected_at).toLocaleDateString()}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-400 mt-1">{anomaly.description || anomaly.title}</p>
                                {anomaly.interpretation && (
                                    <div className="mt-2 text-xs text-gray-300 italic border-l-2 border-white/10 pl-2">
                                        &quot;{anomaly.interpretation}&quot;
                                    </div>
                                )}
                                {anomaly.suggested_action && (
                                    <div className="mt-2 flex items-center gap-2 text-xs text-blue-300">
                                        <Zap className="w-3 h-3" />
                                        <span>Рекомендация: {anomaly.suggested_action}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))
            )}
        </div>
    );
}
