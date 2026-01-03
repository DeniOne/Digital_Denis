'use client';

import React, { useState, useEffect } from 'react';
import { api, AnalyticsSummary, ActivityPoint, MoodData } from '@/lib/api';
import { AnalyticsHeader } from '@/components/analytics/AnalyticsHeader';
import { StatsCards } from '@/components/analytics/StatsCards';
import { TopicsChart } from '@/components/analytics/TopicsChart';
import { MessageTimeline } from '@/components/analytics/MessageTimeline';
import { ActivityHeatmap } from '@/components/analytics/index';
import { MoodChart } from '@/components/analytics/MoodChart';
import { AnomalyList } from '@/components/analytics/AnomalyList';
import { Loader2, AlertCircle, FileText } from 'lucide-react';
import { Anomaly } from '@/lib/api';

export default function AnalyticsPage() {
    const [period, setPeriod] = useState(30);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [activity, setActivity] = useState<ActivityPoint[]>([]);
    const [heatmap, setHeatmap] = useState<ActivityPoint[]>([]);
    const [mood, setMood] = useState<MoodData[]>([]);
    const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

    // Mock user ID for now - should come from auth
    const USER_ID = '00000000-0000-0000-0000-000000000000';

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            setError(null);
            try {
                const [sumRes, actRes, heatRes, moodRes, anomRes] = await Promise.all([
                    api.analytics.getSummary(USER_ID, period),
                    api.analytics.getActivity(USER_ID, period),
                    api.analytics.getHeatmap(USER_ID),
                    api.analytics.getMood(USER_ID, period),
                    api.analytics.getAnomalies('new', 5)
                ]);

                setSummary(sumRes);
                setActivity(actRes);
                setHeatmap(heatRes);
                setMood(moodRes);
                setAnomalies(anomRes);
            } catch (err) {
                console.error('Failed to fetch analytics:', err);
                setError('Не удалось загрузить данные аналитики. Пожалуйста, проверьте подключение к серверу.');
            } finally {
                setLoading(false);
            }
        }

        fetchData();
    }, [period]);

    if (loading && !summary) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                <p className="text-gray-400 animate-pulse">Инициализация нейронных связей...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
                <div className="bg-red-500/10 p-4 rounded-full mb-4">
                    <AlertCircle className="w-12 h-12 text-red-500" />
                </div>
                <h2 className="text-xl font-bold mb-2">Ошибка загрузки</h2>
                <p className="text-gray-400 max-w-md">{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-6 px-6 py-2 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors"
                >
                    Попробовать снова
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-[1400px] mx-auto p-4 md:p-8">
            <AnalyticsHeader period={period} setPeriod={setPeriod} />

            {summary && <StatsCards summary={summary} />}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <div className="bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 md:p-8">
                    <MessageTimeline data={activity} />
                </div>
                <div className="bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 md:p-8">
                    <TopicsChart topics={summary?.top_topics || []} />
                </div>
                <div className="bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 md:p-8 lg:col-span-2">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <span className="w-1.5 h-6 bg-rose-500 rounded-full"></span>
                        Эмоциональный фон
                    </h3>
                    <MoodChart data={mood} />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                <div className="lg:col-span-2 bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 md:p-8">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <span className="w-1.5 h-6 bg-emerald-500 rounded-full"></span>
                        Карта когнитивной активности (365 дней)
                    </h3>
                    <ActivityHeatmap data={heatmap} />
                </div>

                <div className="bg-gray-900/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 md:p-8">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <span className="w-1.5 h-6 bg-amber-500 rounded-full"></span>
                            Аномалии
                        </h3>
                        <button className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 bg-blue-500/10 px-2 py-1 rounded-lg transition-colors">
                            <FileText className="w-3 h-3" />
                            Отчет
                        </button>
                    </div>
                    <AnomalyList anomalies={anomalies} />
                </div>
            </div>

            <div className="mt-8 text-center text-xs text-gray-500">
                Digital Den Cognitive OS — Модуль персональной аналитики
            </div>
        </div>
    );
}
