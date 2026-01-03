'use client';

/**
 * Integrations Settings Component
 * ═══════════════════════════════════════════════════════════════════════════
 */

import { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, XCircle, RefreshCcw, Loader2, ExternalLink } from 'lucide-react';

interface GoogleStatus {
    active: boolean;
    email: string | null;
    expires_at: string | null;
}

export default function IntegrationsSettings() {
    const [status, setStatus] = useState<GoogleStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);

    const fetchStatus = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/v1/auth/google/status');
            const data = await res.json();
            setStatus(data);
        } catch (err) {
            console.error('Failed to fetch Google status:', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const handleConnect = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/v1/auth/google');
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (err) {
            alert('Ошибка при попытке подключения Google Calendar');
        }
    };

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            await fetch('http://localhost:8000/api/v1/auth/google/sync', { method: 'POST' });
            alert('Синхронизация запущена');
        } catch (err) {
            alert('Ошибка при синхронизации');
        } finally {
            setIsSyncing(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="animate-spin text-amber-500" size={32} />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-xl font-semibold text-white mb-1">Интеграции</h2>
                <p className="text-gray-400 text-sm">Подключение внешних сервисов к Digital Den</p>
            </div>

            <div className="grid gap-6">
                {/* Google Calendar Card */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/20 transition-all">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex gap-4">
                            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-400">
                                <Calendar size={28} />
                            </div>
                            <div>
                                <h3 className="text-lg font-medium text-white">Google Calendar</h3>
                                <p className="text-gray-400 text-sm">Синхронизация встреч, задач и напоминаний</p>
                            </div>
                        </div>
                        {status?.active ? (
                            <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-xs font-medium">
                                <CheckCircle2 size={14} /> Подключено
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 px-3 py-1 bg-gray-500/10 text-gray-400 rounded-full text-xs font-medium">
                                <XCircle size={14} /> Не подключено
                            </div>
                        )}
                    </div>

                    {status?.active ? (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="text-sm">
                                    <div className="text-gray-400">Аккаунт:</div>
                                    <div className="text-white font-medium">{status.email || 'Основной профиль'}</div>
                                </div>
                                <button
                                    onClick={handleSync}
                                    disabled={isSyncing}
                                    className="flex items-center gap-2 text-amber-400 hover:text-amber-300 text-sm font-medium transition-colors disabled:opacity-50"
                                >
                                    <RefreshCcw size={16} className={isSyncing ? 'animate-spin' : ''} />
                                    Синхронизировать сейчас
                                </button>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    className="flex-1 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-sm transition-colors border border-white/10"
                                    onClick={() => alert('Отключение в разработке')}
                                >
                                    Отключить
                                </button>
                                <button
                                    className="flex-1 py-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg text-sm font-medium transition-colors"
                                    onClick={handleConnect}
                                >
                                    Переподключить
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <p className="text-gray-400 text-sm italic">
                                Подключите Google Календарь, чтобы Дэн мог видеть ваше расписание и добавлять важные события автоматически.
                            </p>
                            <button
                                onClick={handleConnect}
                                className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                            >
                                <ExternalLink size={18} />
                                Подключить аккаунт Google
                            </button>
                        </div>
                    )}
                </div>

                {/* Placeholder for future integrations */}
                <div className="bg-white/5 border border-dashed border-white/10 rounded-xl p-5 opacity-50 grayscale">
                    <div className="flex gap-4">
                        <div className="w-12 h-12 bg-gray-500/10 rounded-lg flex items-center justify-center text-gray-400">
                            <Share2 size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-medium text-gray-400">Другие сервисы</h3>
                            <p className="text-white/20 text-sm italic">Скоро: Telegram, Notion, Outlook</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Simple Share2 mock for the placeholder
function Share2({ size }: { size: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <circle cx="18" cy="5" r="3" />
            <circle cx="6" cy="12" r="3" />
            <circle cx="18" cy="19" r="3" />
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
    );
}
