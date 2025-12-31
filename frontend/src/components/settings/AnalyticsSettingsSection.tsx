'use client';

/**
 * Analytics Settings Section
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState, useEffect } from 'react';
import { Save, Loader2, Check } from 'lucide-react';
import { useUpdateAnalytics } from '@/lib/hooks';
import type { AnalyticsSettings } from '@/lib/api';

interface Props {
    settings: AnalyticsSettings;
}

const ANALYTICS_TYPES = [
    { value: 'logical_contradictions', label: 'Логические противоречия', description: 'Конфликты между решениями' },
    { value: 'recurring_topics', label: 'Повторяющиеся темы', description: 'Паттерны в мышлении' },
    { value: 'trend_deviation', label: 'Отклонения от трендов', description: 'Аномалии активности' },
    { value: 'cognitive_biases', label: 'Когнитивные искажения', description: 'Систематические ошибки' },
    { value: 'focus_loss', label: 'Потеря фокуса', description: 'Рассеянность внимания' },
];

const AGGRESSIVENESS_LEVELS = [
    { value: 'inform', label: 'Информировать', description: 'Тихие уведомления' },
    { value: 'recommend', label: 'Рекомендовать', description: 'Предлагать действия' },
    { value: 'warn', label: 'Предупреждать', description: 'Выделенные алерты' },
    { value: 'demand_attention', label: 'Требовать внимания', description: 'Блокирующие уведомления' },
];

export default function AnalyticsSettingsSection({ settings }: Props) {
    const [form, setForm] = useState(settings);
    const [hasChanges, setHasChanges] = useState(false);
    const updateMutation = useUpdateAnalytics();

    useEffect(() => {
        setForm(settings);
    }, [settings]);

    useEffect(() => {
        const changed = JSON.stringify(form) !== JSON.stringify(settings);
        setHasChanges(changed);
    }, [form, settings]);

    const handleSave = async () => {
        await updateMutation.mutateAsync(form);
        setHasChanges(false);
    };

    const toggleType = (type: string) => {
        const types = form.analytics_types || [];
        if (types.includes(type)) {
            setForm({ ...form, analytics_types: types.filter(t => t !== type) });
        } else {
            setForm({ ...form, analytics_types: [...types, type] });
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Аналитика</h2>
                    <p className="text-gray-400 text-sm">Какие инсайты генерировать</p>
                </div>
                {hasChanges && (
                    <button
                        onClick={handleSave}
                        disabled={updateMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                        {updateMutation.isPending ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <Save size={16} />
                        )}
                        Сохранить
                    </button>
                )}
            </div>

            {/* Analytics Types */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Типы анализа</label>
                <div className="space-y-2">
                    {ANALYTICS_TYPES.map((type) => (
                        <label
                            key={type.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.analytics_types?.includes(type.value)
                                    ? 'border-purple-500 bg-purple-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="checkbox"
                                checked={form.analytics_types?.includes(type.value) || false}
                                onChange={() => toggleType(type.value)}
                                className="sr-only"
                            />
                            <div className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center ${form.analytics_types?.includes(type.value)
                                    ? 'border-purple-500 bg-purple-500'
                                    : 'border-gray-500'
                                }`}>
                                {form.analytics_types?.includes(type.value) && (
                                    <Check size={14} className="text-white" />
                                )}
                            </div>
                            <div>
                                <div className="text-white font-medium">{type.label}</div>
                                <div className="text-gray-400 text-sm">{type.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Aggressiveness */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Интенсивность уведомлений</label>
                <div className="space-y-2">
                    {AGGRESSIVENESS_LEVELS.map((level) => (
                        <label
                            key={level.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.analytics_aggressiveness === level.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="analytics_aggressiveness"
                                value={level.value}
                                checked={form.analytics_aggressiveness === level.value}
                                onChange={(e) => setForm({ ...form, analytics_aggressiveness: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.analytics_aggressiveness === level.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.analytics_aggressiveness === level.value && (
                                    <div className="w-2 h-2 rounded-full bg-amber-500" />
                                )}
                            </div>
                            <div>
                                <div className="text-white font-medium">{level.label}</div>
                                <div className="text-gray-400 text-sm">{level.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>
        </div>
    );
}
