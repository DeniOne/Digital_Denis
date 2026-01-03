/**
 * Digital Den — Kaizen Settings Section
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Settings for Kaizen Engine: Adaptive AI, Mirror, Comparison Period
 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Check, AlertCircle, Brain, Eye, Calendar } from 'lucide-react';
import client from '@/lib/api';

interface KaizenSettings {
    adaptive_ai_enabled: boolean;
    show_mirror: boolean;
    comparison_period: string;
    period_options: Array<{
        value: string;
        label: string;
        days: number | null;
    }>;
}

export default function KaizenSettingsSection() {
    const queryClient = useQueryClient();
    const [localSettings, setLocalSettings] = useState<Partial<KaizenSettings>>({});

    const { data: settings, isLoading, error } = useQuery<KaizenSettings>({
        queryKey: ['settings', 'kaizen'],
        queryFn: async () => {
            const res = await client.get<KaizenSettings>('/settings/kaizen');
            return res.data;
        },
    });

    const mutation = useMutation({
        mutationFn: async (data: Partial<KaizenSettings>) => {
            const res = await client.patch('/settings/kaizen', data);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings', 'kaizen'] });
        },
    });

    useEffect(() => {
        if (settings) {
            setLocalSettings({
                adaptive_ai_enabled: settings.adaptive_ai_enabled,
                show_mirror: settings.show_mirror,
                comparison_period: settings.comparison_period,
            });
        }
    }, [settings]);

    const handleToggle = (field: 'adaptive_ai_enabled' | 'show_mirror') => {
        const newValue = !localSettings[field];
        setLocalSettings(prev => ({ ...prev, [field]: newValue }));
        mutation.mutate({ ...localSettings, [field]: newValue });
    };

    const handlePeriodChange = (period: string) => {
        setLocalSettings(prev => ({ ...prev, comparison_period: period }));
        mutation.mutate({ ...localSettings, comparison_period: period });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="animate-spin text-amber-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center gap-2 text-red-400 py-8">
                <AlertCircle size={20} />
                <span>Не удалось загрузить настройки Kaizen</span>
            </div>
        );
    }

    const periodOptions = settings?.period_options || [
        { value: 'week', label: 'Неделя', days: 7 },
        { value: 'month', label: 'Месяц', days: 30 },
        { value: 'quarter', label: 'Квартал', days: 90 },
        { value: 'half_year', label: 'Полгода', days: 180 },
        { value: 'year', label: 'Год', days: 365 },
        { value: 'all_time', label: 'Всё время', days: null },
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h2 className="text-xl font-semibold text-white mb-2">Kaizen Engine</h2>
                <p className="text-gray-400 text-sm">
                    Настройки отслеживания когнитивной динамики
                </p>
            </div>

            {/* Adaptive AI Toggle */}
            <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <Brain size={16} className="text-amber-500" />
                    Адаптивное поведение ИИ
                </h3>
                <div
                    className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer ${localSettings.adaptive_ai_enabled
                            ? 'bg-amber-500/10 border-amber-500/30'
                            : 'bg-zinc-800/50 border-zinc-700'
                        }`}
                    onClick={() => handleToggle('adaptive_ai_enabled')}
                >
                    <div>
                        <div className="font-medium text-white">
                            {localSettings.adaptive_ai_enabled ? 'Включено' : 'Выключено'}
                        </div>
                        <div className="text-sm text-gray-400">
                            ИИ адаптирует стиль ответов под твоё текущее состояние
                        </div>
                    </div>
                    <div className={`w-12 h-6 rounded-full transition-all relative ${localSettings.adaptive_ai_enabled ? 'bg-amber-500' : 'bg-zinc-600'
                        }`}>
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${localSettings.adaptive_ai_enabled ? 'left-7' : 'left-1'
                            }`} />
                    </div>
                </div>
                <p className="text-xs text-gray-500 pl-1">
                    Режимы: Стратег, Аналитик, Коуч, Фиксатор — выбираются автоматически
                </p>
            </div>

            {/* Show Mirror Toggle */}
            <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <Eye size={16} className="text-purple-500" />
                    Kaizen-зеркало
                </h3>
                <div
                    className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer ${localSettings.show_mirror
                            ? 'bg-purple-500/10 border-purple-500/30'
                            : 'bg-zinc-800/50 border-zinc-700'
                        }`}
                    onClick={() => handleToggle('show_mirror')}
                >
                    <div>
                        <div className="font-medium text-white">
                            {localSettings.show_mirror ? 'Показывать' : 'Скрыть'}
                        </div>
                        <div className="text-sm text-gray-400">
                            Рефлексивные наблюдения без оценок и рекомендаций
                        </div>
                    </div>
                    <div className={`w-12 h-6 rounded-full transition-all relative ${localSettings.show_mirror ? 'bg-purple-500' : 'bg-zinc-600'
                        }`}>
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${localSettings.show_mirror ? 'left-7' : 'left-1'
                            }`} />
                    </div>
                </div>
            </div>

            {/* Comparison Period */}
            <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <Calendar size={16} className="text-blue-500" />
                    Период сравнения
                </h3>
                <p className="text-sm text-gray-500">
                    Основной период для расчёта динамики Kaizen-индекса
                </p>
                <div className="grid grid-cols-3 gap-3">
                    {periodOptions.map((option) => (
                        <button
                            key={option.value}
                            onClick={() => handlePeriodChange(option.value)}
                            className={`p-3 rounded-lg border transition-all ${localSettings.comparison_period === option.value
                                    ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                                    : 'bg-zinc-800/50 border-zinc-700 text-gray-400 hover:border-zinc-600'
                                }`}
                        >
                            <div className="font-medium">{option.label}</div>
                            <div className="text-xs opacity-60">
                                {option.days ? `${option.days}д` : '∞'}
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Info Note */}
            <div className="bg-zinc-800/30 rounded-lg p-4 border border-zinc-700">
                <div className="flex items-start gap-3">
                    <div className="text-lg">💡</div>
                    <div>
                        <div className="font-medium text-white text-sm mb-1">Философия Kaizen</div>
                        <div className="text-xs text-gray-400">
                            Kaizen Engine наблюдает, а не оценивает. Сравнение только с самим собой:
                            ты сегодня ↔ ты вчера. Никаких норм, никаких рекомендаций.
                        </div>
                    </div>
                </div>
            </div>

            {/* Saving Indicator */}
            {mutation.isPending && (
                <div className="flex items-center gap-2 text-amber-400 text-sm">
                    <Loader2 size={14} className="animate-spin" />
                    Сохранение...
                </div>
            )}
            {mutation.isSuccess && (
                <div className="flex items-center gap-2 text-green-400 text-sm">
                    <Check size={14} />
                    Сохранено
                </div>
            )}
        </div>
    );
}
