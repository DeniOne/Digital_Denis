'use client';

/**
 * Autonomy Settings Section
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState, useEffect } from 'react';
import { Save, Loader2, Check } from 'lucide-react';
import { useUpdateAutonomy } from '@/lib/hooks';
import type { AutonomySettings as AutonomySettingsType } from '@/lib/api';

interface Props {
    settings: AutonomySettingsType;
}

const INITIATIVE_LEVELS = [
    { value: 'request_only', label: 'Только по запросу', description: 'ИИ молчит, пока не спросишь' },
    { value: 'suggest', label: 'Предлагать идеи', description: 'Инициирует полезные предложения' },
    { value: 'warn', label: 'Предупреждать о проблемах', description: 'Указывает на риски и противоречия' },
    { value: 'proactive', label: 'Проактивный', description: 'Самостоятельно формирует инсайты' },
];

const INTERVENTION_FREQUENCIES = [
    { value: 'realtime', label: 'В реальном времени', description: 'Прямо в чате' },
    { value: 'post_session', label: 'После сессии', description: 'Сводка в конце разговора' },
    { value: 'daily_review', label: 'Ежедневный обзор', description: 'Раз в день' },
    { value: 'anomaly_detected', label: 'При аномалиях', description: 'Только когда что-то не так' },
];

const ALLOWED_ACTIONS = [
    { value: 'create_decisions', label: 'Создавать решения', description: 'Фиксировать принятые решения' },
    { value: 'link_memories', label: 'Связывать воспоминания', description: 'Находить связи между записями' },
    { value: 'refactor_thoughts', label: 'Рефакторить мысли', description: 'Объединять и структурировать' },
    { value: 'challenge_beliefs', label: '⚠️ Оспаривать убеждения', description: 'Критиковать устоявшиеся взгляды' },
];

export default function AutonomySettings({ settings }: Props) {
    const [form, setForm] = useState(settings);
    const [hasChanges, setHasChanges] = useState(false);
    const updateMutation = useUpdateAutonomy();

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

    const toggleAction = (action: string) => {
        const actions = form.allowed_actions || [];
        if (actions.includes(action)) {
            setForm({ ...form, allowed_actions: actions.filter(a => a !== action) });
        } else {
            setForm({ ...form, allowed_actions: [...actions, action] });
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Автономность</h2>
                    <p className="text-gray-400 text-sm">Насколько ИИ может действовать самостоятельно</p>
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

            {/* Initiative Level */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Уровень инициативы</label>
                <div className="space-y-2">
                    {INITIATIVE_LEVELS.map((level) => (
                        <label
                            key={level.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.initiative_level === level.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="initiative_level"
                                value={level.value}
                                checked={form.initiative_level === level.value}
                                onChange={(e) => setForm({ ...form, initiative_level: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.initiative_level === level.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.initiative_level === level.value && (
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

            {/* Intervention Frequency */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Частота вмешательств</label>
                <div className="grid grid-cols-2 gap-2">
                    {INTERVENTION_FREQUENCIES.map((freq) => (
                        <label
                            key={freq.value}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${form.intervention_frequency === freq.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="intervention_frequency"
                                value={freq.value}
                                checked={form.intervention_frequency === freq.value}
                                onChange={(e) => setForm({ ...form, intervention_frequency: e.target.value })}
                                className="sr-only"
                            />
                            <div className="text-white font-medium">{freq.label}</div>
                            <div className="text-gray-400 text-xs">{freq.description}</div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Allowed Actions */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Разрешённые действия</label>
                <div className="space-y-2">
                    {ALLOWED_ACTIONS.map((action) => (
                        <label
                            key={action.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.allowed_actions?.includes(action.value)
                                    ? 'border-green-500 bg-green-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="checkbox"
                                checked={form.allowed_actions?.includes(action.value) || false}
                                onChange={() => toggleAction(action.value)}
                                className="sr-only"
                            />
                            <div className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center ${form.allowed_actions?.includes(action.value)
                                    ? 'border-green-500 bg-green-500'
                                    : 'border-gray-500'
                                }`}>
                                {form.allowed_actions?.includes(action.value) && (
                                    <Check size={14} className="text-black" />
                                )}
                            </div>
                            <div>
                                <div className="text-white font-medium">{action.label}</div>
                                <div className="text-gray-400 text-sm">{action.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>
        </div>
    );
}
