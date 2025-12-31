'use client';

/**
 * Settings Page — AI Control & Rules Engine
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState } from 'react';
import {
    Bot, Brain, Database, BarChart3, ScrollText,
    Loader2, Save, ChevronRight, Share2, Calendar
} from 'lucide-react';
import { useSettings, useRules, useUpdateSettings } from '@/lib/hooks';
import BehaviorSettings from '@/components/settings/BehaviorSettings';
import AutonomySettings from '@/components/settings/AutonomySettings';
import MemorySettingsSection from '@/components/settings/MemorySettingsSection';
import AnalyticsSettingsSection from '@/components/settings/AnalyticsSettingsSection';
import RulesEngine from '@/components/settings/RulesEngine';
import IntegrationsSettings from '@/components/settings/IntegrationsSettings';

type TabId = 'behavior' | 'autonomy' | 'memory' | 'analytics' | 'rules' | 'integrations';

interface Tab {
    id: TabId;
    label: string;
    icon: React.ReactNode;
    description: string;
}

const tabs: Tab[] = [
    { id: 'behavior', label: 'Поведение ИИ', icon: <Bot size={20} />, description: 'Роль, стиль мышления, конфронтация' },
    { id: 'autonomy', label: 'Автономность', icon: <Brain size={20} />, description: 'Инициатива и разрешённые действия' },
    { id: 'memory', label: 'Память', icon: <Database size={20} />, description: 'Политика хранения и доверие' },
    { id: 'analytics', label: 'Аналитика', icon: <BarChart3 size={20} />, description: 'Типы анализа и уведомления' },
    { id: 'rules', label: 'Правила', icon: <ScrollText size={20} />, description: 'Персональные правила для ИИ' },
    { id: 'integrations', label: 'Интеграции', icon: <Share2 size={20} />, description: 'Google Calendar, Telegram и др.' },
];

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<TabId>('behavior');
    const { data: settings, isLoading, error } = useSettings();
    const { data: rules } = useRules();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-amber-500" size={40} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full text-red-400">
                Ошибка загрузки настроек
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Настройки</h1>
                <p className="text-gray-400">
                    Управление поведением ИИ и персональные правила
                </p>
            </div>

            <div className="flex gap-6">
                {/* Sidebar Navigation */}
                <nav className="w-64 flex-shrink-0">
                    <ul className="space-y-1">
                        {tabs.map((tab) => (
                            <li key={tab.id}>
                                <button
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === tab.id
                                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                            : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                        }`}
                                >
                                    {tab.icon}
                                    <div className="flex-1 text-left">
                                        <div className="font-medium">{tab.label}</div>
                                        <div className="text-xs opacity-60">{tab.description}</div>
                                    </div>
                                    <ChevronRight
                                        size={16}
                                        className={activeTab === tab.id ? 'opacity-100' : 'opacity-0'}
                                    />
                                </button>
                            </li>
                        ))}
                    </ul>

                    {/* Rules Count Badge */}
                    {rules && rules.length > 0 && (
                        <div className="mt-4 px-4 py-2 bg-white/5 rounded-lg">
                            <span className="text-gray-400 text-sm">
                                Активных правил: <span className="text-amber-400">{rules.filter(r => r.is_active).length}</span>
                            </span>
                        </div>
                    )}
                </nav>

                {/* Content Area */}
                <div className="flex-1 bg-white/5 rounded-xl border border-white/10 p-6">
                    {settings && (
                        <>
                            {activeTab === 'behavior' && (
                                <BehaviorSettings settings={settings.behavior} />
                            )}
                            {activeTab === 'autonomy' && (
                                <AutonomySettings settings={settings.autonomy} />
                            )}
                            {activeTab === 'memory' && (
                                <MemorySettingsSection settings={settings.memory} />
                            )}
                            {activeTab === 'analytics' && (
                                <AnalyticsSettingsSection settings={settings.analytics} />
                            )}
                            {activeTab === 'rules' && (
                                <RulesEngine />
                            )}
                            {activeTab === 'integrations' && (
                                <IntegrationsSettings />
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
