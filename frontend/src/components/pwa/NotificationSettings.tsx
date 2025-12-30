'use client';

import { useState, useEffect } from 'react';
import { Bell, BellOff, Loader2 } from 'lucide-react';
import { subscribeToPush, unsubscribeFromPush } from '@/lib/push';

export function NotificationSettings() {
    const [isSupported, setIsSupported] = useState(false);
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            setIsSupported(true);
            checkSubscription();
        } else {
            setIsLoading(false);
        }
    }, []);

    const checkSubscription = async () => {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            setIsSubscribed(!!subscription);
        } catch (e) {
            console.error('Error checking subscription', e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleToggle = async () => {
        setIsLoading(true);
        if (isSubscribed) {
            const success = await unsubscribeFromPush();
            if (success) setIsSubscribed(false);
        } else {
            const success = await subscribeToPush();
            if (success) setIsSubscribed(true);
        }
        setIsLoading(false);
    };

    // ... inside NotificationSettings component ...
    const [quietStart, setQuietStart] = useState('23:00');
    const [quietEnd, setQuietEnd] = useState('08:00');
    const [showSettings, setShowSettings] = useState(false);

    // Mock checking settings from backend (TODO: Implement actual API fetch)
    useEffect(() => {
        // api.users.getSettings().then(...)
    }, []);

    const saveSettings = async () => {
        // await api.users.updateSettings({ quiet_hours_start: quietStart, quiet_hours_end: quietEnd });
        setShowSettings(false);
    };

    if (!isSupported) return null;

    return (
        <div className="flex flex-col gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
            <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800">
                    {isSubscribed ? <Bell className="h-5 w-5 text-blue-400" /> : <BellOff className="h-5 w-5 text-zinc-400" />}
                </div>

                <div className="flex-1">
                    <h3 className="font-medium text-zinc-200">Уведомления</h3>
                    <p className="text-xs text-zinc-400">
                        {isSubscribed
                            ? 'Получайте напоминания и инсайты'
                            : 'Включите, чтобы не пропустить важное'}
                    </p>
                </div>

                <button
                    onClick={handleToggle}
                    disabled={isLoading}
                    className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${isSubscribed
                        ? 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                        : 'bg-blue-600 text-white hover:bg-blue-500'
                        } disabled:opacity-50`}
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isSubscribed ? (
                        'Отключить'
                    ) : (
                        'Включить'
                    )}
                </button>
            </div>

            {isSubscribed && (
                <div className="mt-2 border-t border-zinc-800 pt-2">
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="text-xs text-zinc-500 hover:text-zinc-300"
                    >
                        {showSettings ? 'Скрыть настройки' : 'Настроить тихое время'}
                    </button>

                    {showSettings && (
                        <div className="mt-2 flex items-center gap-2 text-sm text-zinc-400">
                            <span>Тихий час с</span>
                            <input
                                type="time"
                                value={quietStart}
                                onChange={(e) => setQuietStart(e.target.value)}
                                className="rounded bg-zinc-800 px-2 py-1 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <span>до</span>
                            <input
                                type="time"
                                value={quietEnd}
                                onChange={(e) => setQuietEnd(e.target.value)}
                                className="rounded bg-zinc-800 px-2 py-1 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <button
                                onClick={saveSettings}
                                className="ml-auto rounded bg-zinc-800 px-3 py-1 text-xs hover:bg-zinc-700"
                            >
                                Сохранить
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
