'use client';

/**
 * Memory Settings Section
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState, useEffect } from 'react';
import { Save, Loader2, Check } from 'lucide-react';
import { useUpdateMemorySettings } from '@/lib/hooks';
import type { MemorySettings } from '@/lib/api';

interface Props {
    settings: MemorySettings;
}

const SAVE_POLICIES = [
    { value: 'save_all', label: 'Сохранять всё', description: 'Каждое сообщение в память' },
    { value: 'save_confirmed', label: 'С подтверждением', description: 'Спрашивать перед сохранением' },
    { value: 'save_marked', label: 'Только отмеченное', description: 'Явно выбранные пользователем' },
];

const TRUST_LEVELS = [
    { value: 'none', label: 'Не доверять', description: 'Не использовать прошлые записи' },
    { value: 'cautious', label: 'Осторожно', description: 'Использовать с оговорками' },
    { value: 'trusted', label: 'Полное доверие', description: 'Свободно ссылаться и спорить' },
];

const SAVED_TYPES = [
    { value: 'facts', label: 'Факты' },
    { value: 'decisions', label: 'Решения' },
    { value: 'hypotheses', label: 'Гипотезы' },
    { value: 'emotional_states', label: 'Эмоции' },
    { value: 'behavioral_patterns', label: 'Паттерны' },
];

export default function MemorySettingsSection({ settings }: Props) {
    const [form, setForm] = useState(settings);
    const [hasChanges, setHasChanges] = useState(false);
    const updateMutation = useUpdateMemorySettings();

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
        const types = form.saved_types || [];
        if (types.includes(type)) {
            setForm({ ...form, saved_types: types.filter(t => t !== type) });
        } else {
            setForm({ ...form, saved_types: [...types, type] });
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Память</h2>
                    <p className="text-gray-400 text-sm">Что и как сохранять</p>
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

            {/* Save Policy */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Политика сохранения</label>
                <div className="space-y-2">
                    {SAVE_POLICIES.map((policy) => (
                        <label
                            key={policy.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.save_policy === policy.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="save_policy"
                                value={policy.value}
                                checked={form.save_policy === policy.value}
                                onChange={(e) => setForm({ ...form, save_policy: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.save_policy === policy.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.save_policy === policy.value && (
                                    <div className="w-2 h-2 rounded-full bg-amber-500" />
                                )}
                            </div>
                            <div>
                                <div className="text-white font-medium">{policy.label}</div>
                                <div className="text-gray-400 text-sm">{policy.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Auto Archive */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Автоархивация (дней)</label>
                <input
                    type="range"
                    min="0"
                    max="365"
                    step="30"
                    value={form.auto_archive_days}
                    onChange={(e) => setForm({ ...form, auto_archive_days: parseInt(e.target.value) })}
                    className="w-full accent-amber-500"
                />
                <div className="flex justify-between text-sm text-gray-400">
                    <span>Отключено</span>
                    <span className="text-amber-400 font-medium">
                        {form.auto_archive_days === 0 ? 'Никогда' : `${form.auto_archive_days} дней`}
                    </span>
                    <span>1 год</span>
                </div>
            </div>

            {/* Trust Level */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Доверие к памяти</label>
                <div className="space-y-2">
                    {TRUST_LEVELS.map((level) => (
                        <label
                            key={level.value}
                            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${form.memory_trust_level === level.value
                                    ? 'border-amber-500 bg-amber-500/10'
                                    : 'border-white/10 hover:border-white/20'
                                }`}
                        >
                            <input
                                type="radio"
                                name="memory_trust_level"
                                value={level.value}
                                checked={form.memory_trust_level === level.value}
                                onChange={(e) => setForm({ ...form, memory_trust_level: e.target.value })}
                                className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${form.memory_trust_level === level.value ? 'border-amber-500' : 'border-gray-500'
                                }`}>
                                {form.memory_trust_level === level.value && (
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

            {/* Saved Types */}
            <div className="space-y-3">
                <label className="block text-white font-medium">Типы для сохранения</label>
                <div className="flex flex-wrap gap-2">
                    {SAVED_TYPES.map((type) => (
                        <label
                            key={type.value}
                            className={`px-4 py-2 rounded-full border cursor-pointer transition-all ${form.saved_types?.includes(type.value)
                                    ? 'border-green-500 bg-green-500/20 text-green-400'
                                    : 'border-white/20 text-gray-400 hover:border-white/40'
                                }`}
                        >
                            <input
                                type="checkbox"
                                checked={form.saved_types?.includes(type.value) || false}
                                onChange={() => toggleType(type.value)}
                                className="sr-only"
                            />
                            {type.label}
                        </label>
                    ))}
                </div>
            </div>
        </div>
    );
}
