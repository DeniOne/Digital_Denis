'use client';

/**
 * Rules Engine Section
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState } from 'react';
import { Plus, Trash2, Power, Edit2, Save, X, Loader2 } from 'lucide-react';
import { useRules, useCreateRule, useDeleteRule, useToggleRule, useUpdateRule } from '@/lib/hooks';
import type { Rule, RuleCreate } from '@/lib/api';

const PRIORITIES = [
    { value: 'low', label: 'Низкий', color: 'text-gray-400' },
    { value: 'normal', label: 'Обычный', color: 'text-blue-400' },
    { value: 'high', label: 'Высокий', color: 'text-red-400' },
];

export default function RulesEngine() {
    const { data: rules, isLoading } = useRules();
    const createMutation = useCreateRule();
    const deleteMutation = useDeleteRule();
    const toggleMutation = useToggleRule();
    const updateMutation = useUpdateRule();

    const [isCreating, setIsCreating] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [newRule, setNewRule] = useState<RuleCreate>({
        instruction: '',
        scope: 'global',
        trigger: 'always',
        priority: 'normal',
    });

    const globalRules = rules?.filter(r => r.scope === 'global') || [];
    const contextRules = rules?.filter(r => r.scope === 'context') || [];

    const handleCreate = async () => {
        if (!newRule.instruction.trim()) return;
        await createMutation.mutateAsync(newRule);
        setNewRule({ instruction: '', scope: 'global', trigger: 'always', priority: 'normal' });
        setIsCreating(false);
    };

    const handleDelete = async (id: string) => {
        if (confirm('Удалить правило?')) {
            await deleteMutation.mutateAsync(id);
        }
    };

    const handleToggle = async (id: string) => {
        await toggleMutation.mutateAsync(id);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="animate-spin text-amber-500" size={32} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Правила</h2>
                    <p className="text-gray-400 text-sm">Персональные инструкции для ИИ</p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg font-medium transition-colors"
                >
                    <Plus size={16} />
                    Добавить правило
                </button>
            </div>

            {/* Create New Rule */}
            {isCreating && (
                <div className="p-4 border border-amber-500/30 bg-amber-500/5 rounded-lg space-y-4">
                    <div>
                        <label className="block text-white text-sm font-medium mb-2">Инструкция</label>
                        <textarea
                            value={newRule.instruction}
                            onChange={(e) => setNewRule({ ...newRule, instruction: e.target.value })}
                            placeholder="Например: Не соглашайся со мной автоматически"
                            className="w-full bg-black/30 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none resize-none"
                            rows={3}
                        />
                    </div>
                    <div className="flex gap-4">
                        <div className="flex-1">
                            <label className="block text-white text-sm font-medium mb-2">Область</label>
                            <select
                                value={newRule.scope}
                                onChange={(e) => setNewRule({ ...newRule, scope: e.target.value })}
                                className="w-full bg-black/30 border border-white/20 rounded-lg px-4 py-2 text-white focus:border-amber-500 focus:outline-none"
                            >
                                <option value="global">Глобальное</option>
                                <option value="context">Контекстное</option>
                            </select>
                        </div>
                        <div className="flex-1">
                            <label className="block text-white text-sm font-medium mb-2">Приоритет</label>
                            <select
                                value={newRule.priority}
                                onChange={(e) => setNewRule({ ...newRule, priority: e.target.value })}
                                className="w-full bg-black/30 border border-white/20 rounded-lg px-4 py-2 text-white focus:border-amber-500 focus:outline-none"
                            >
                                <option value="low">Низкий</option>
                                <option value="normal">Обычный</option>
                                <option value="high">Высокий</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <button
                            onClick={() => setIsCreating(false)}
                            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                        >
                            Отмена
                        </button>
                        <button
                            onClick={handleCreate}
                            disabled={!newRule.instruction.trim() || createMutation.isPending}
                            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {createMutation.isPending ? (
                                <Loader2 size={16} className="animate-spin" />
                            ) : (
                                <Save size={16} />
                            )}
                            Создать
                        </button>
                    </div>
                </div>
            )}

            {/* Global Rules */}
            <div className="space-y-3">
                <h3 className="text-white font-medium flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                    Глобальные правила
                    <span className="text-gray-500 text-sm">({globalRules.length})</span>
                </h3>
                {globalRules.length === 0 ? (
                    <p className="text-gray-500 text-sm py-4">Нет глобальных правил</p>
                ) : (
                    <div className="space-y-2">
                        {globalRules.map((rule) => (
                            <RuleCard
                                key={rule.id}
                                rule={rule}
                                onToggle={() => handleToggle(rule.id)}
                                onDelete={() => handleDelete(rule.id)}
                                isToggling={toggleMutation.isPending}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Context Rules */}
            <div className="space-y-3">
                <h3 className="text-white font-medium flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                    Контекстные правила
                    <span className="text-gray-500 text-sm">({contextRules.length})</span>
                </h3>
                {contextRules.length === 0 ? (
                    <p className="text-gray-500 text-sm py-4">Нет контекстных правил</p>
                ) : (
                    <div className="space-y-2">
                        {contextRules.map((rule) => (
                            <RuleCard
                                key={rule.id}
                                rule={rule}
                                onToggle={() => handleToggle(rule.id)}
                                onDelete={() => handleDelete(rule.id)}
                                isToggling={toggleMutation.isPending}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

interface RuleCardProps {
    rule: Rule;
    onToggle: () => void;
    onDelete: () => void;
    isToggling: boolean;
}

function RuleCard({ rule, onToggle, onDelete, isToggling }: RuleCardProps) {
    const priorityInfo = PRIORITIES.find(p => p.value === rule.priority) || PRIORITIES[1];

    return (
        <div className={`p-4 rounded-lg border transition-all ${rule.is_active
                ? 'border-white/20 bg-white/5'
                : 'border-white/10 bg-white/[0.02] opacity-60'
            }`}>
            <div className="flex items-start gap-3">
                <button
                    onClick={onToggle}
                    disabled={isToggling}
                    className={`mt-1 p-1 rounded transition-colors ${rule.is_active
                            ? 'text-green-400 hover:bg-green-500/20'
                            : 'text-gray-500 hover:bg-white/10'
                        }`}
                    title={rule.is_active ? 'Отключить' : 'Включить'}
                >
                    <Power size={18} />
                </button>
                <div className="flex-1">
                    <p className="text-white">{rule.instruction}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs">
                        <span className={priorityInfo.color}>
                            {priorityInfo.label}
                        </span>
                        {rule.context_mode && (
                            <span className="text-purple-400">
                                Режим: {rule.context_mode}
                            </span>
                        )}
                    </div>
                </div>
                <button
                    onClick={onDelete}
                    className="p-1 text-gray-500 hover:text-red-400 hover:bg-red-500/20 rounded transition-colors"
                    title="Удалить"
                >
                    <Trash2 size={18} />
                </button>
            </div>
        </div>
    );
}
