'use client';

/**
 * Behavior Settings Section
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState, useEffect } from 'react';
import { Save, Loader2 } from 'lucide-react';
import { useUpdateBehavior } from '@/lib/hooks';
import type { BehaviorSettings as BehaviorSettingsType } from '@/lib/api';

interface Props {
    settings: BehaviorSettingsType;
}

const AI_ROLES = [
    { value: 'partner_strategic', label: 'Партнёр-стратег', description: 'Равный партнёр в принятии решений' },
    { value: 'analyst_logical', label: 'Логический аналитик', description: 'Фокус на анализе и структурировании' },
    { value: 'coach_socratic', label: 'Коуч (сократический)', description: 'Вопросы важнее ответов' },
    { value: 'recorder_passive', label: 'Фиксатор', description: 'Минимальное вмешательство' },
    { value: 'explorer_hypothesis', label: 'Исследователь гипотез', description: 'Генерация идей и предположений' },
];

const THINKING_DEPTHS = [
    { value: 'shallow', label: 'Поверхностный', description: 'Быстрые короткие ответы' },
    { value: 'structured', label: 'Структурированный', description: 'Логичные пошаговые объяснения' },
    { value: 'systemic', label: 'Системный', description: 'Глубокий анализ взаимосвязей' },
    { value: 'philosophical', label: 'Философский', description: 'Максимальная глубина рефлексии' },
];

const RESPONSE_STYLES = [
    { value: 'short', label: 'Краткий' },
    { value: 'detailed', label: 'Подробный' },
];

const CONFRONTATION_LEVELS = [
    { value: 'none', label: 'Никогда не спорить', description: 'Всегда соглашаться' },
    { value: 'soft', label: 'Мягко указывать', description: 'Осторожные замечания' },
    { value: 'argumented', label: 'Аргументировано возражать', description: 'Логические контраргументы' },
    { value: 'hard', label: 'Жёстко останавливать', description: 'Блокировать логические ошибки' },
];

export default function BehaviorSettings({ settings }: Props) {
    const [form, setForm] = useState(settings);
    const [hasChanges, setHasChanges] = useState(false);
    const updateMutation = useUpdateBehavior();

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

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Поведение ИИ</h2>
                    <p className="text-gray-400 text-sm">Как ИИ думает и отвечает</p>
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

            {/* AI Role */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Роль ИИ</label>
                <div className="grid gap-2">
                    {AI_ROLES.map((role) => (
                        <label
                            key={role.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.ai_role === role.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="ai_role"
                                value={role.value}
                                checked={form.ai_role === role.value}
                                onChange={(e) => setForm({ ...form, ai_role: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.ai_role === role.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.ai_role === role.value && (
                                    <div className="w-2 h-2 rounded-full bg-amber-500" />
                                )}
                            </div>
                            <div>
                                <div className="text-white font-medium">{role.label}</div>
                                <div className="text-gray-400 text-sm">{role.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Thinking Depth */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Глубина мышления</label>
                <div className="grid grid-cols-2 gap-2">
                    {THINKING_DEPTHS.map((depth) => (
                        <label
                            key={depth.value}
                            className={`p-3 rounded-lg border cursor-pointer transition-all text-center ${form.thinking_depth === depth.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="thinking_depth"
                                value={depth.value}
                                checked={form.thinking_depth === depth.value}
                                onChange={(e) => setForm({ ...form, thinking_depth: e.target.value })}
                                className="sr-only"
                            />
                            <div className="text-white font-medium">{depth.label}</div>
                            <div className="text-gray-400 text-xs">{depth.description}</div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Response Style */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Стиль ответов</label>
                <div className="flex gap-4">
                    {RESPONSE_STYLES.map((style) => (
                        <label
                            key={style.value}
                            className={`flex-1 p-3 rounded-lg border cursor-pointer transition-all text-center ${form.response_style === style.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="response_style"
                                value={style.value}
                                checked={form.response_style === style.value}
                                onChange={(e) => setForm({ ...form, response_style: e.target.value })}
                                className="sr-only"
                            />
                            <div className="text-white font-medium">{style.label}</div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Confrontation Level */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Уровень конфронтации</label>
                <div className="space-y-2">
                    {CONFRONTATION_LEVELS.map((level) => (
                        <label
                            key={level.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.confrontation_level === level.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="confrontation_level"
                                value={level.value}
                                checked={form.confrontation_level === level.value}
                                onChange={(e) => setForm({ ...form, confrontation_level: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.confrontation_level === level.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.confrontation_level === level.value && (
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
