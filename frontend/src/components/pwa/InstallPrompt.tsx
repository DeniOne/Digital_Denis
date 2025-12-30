'use client';

import { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallPrompt() {
    const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
    const [showPrompt, setShowPrompt] = useState(false);
    const [isInstalled, setIsInstalled] = useState(false);

    useEffect(() => {
        // Проверяем, установлено ли приложение
        // Проверяем, установлено ли приложение
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        if (isStandalone) {
            setIsInstalled((prev) => {
                if (!prev) return true;
                return prev;
            });
            return;
        }

        // Проверяем, было ли уже закрыто предложение
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed, 10);
            // Показываем снова через 7 дней
            if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
                return;
            }
        }

        const handler = (e: Event) => {
            e.preventDefault();
            setDeferredPrompt(e as BeforeInstallPromptEvent);
            // Показываем баннер с небольшой задержкой
            setTimeout(() => setShowPrompt(true), 2000);
        };

        window.addEventListener('beforeinstallprompt', handler);

        // Отслеживаем успешную установку
        window.addEventListener('appinstalled', () => {
            setIsInstalled(true);
            setShowPrompt(false);
            setDeferredPrompt(null);
        });

        return () => {
            window.removeEventListener('beforeinstallprompt', handler);
        };
    }, []);

    const handleInstall = async () => {
        if (!deferredPrompt) return;

        await deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;

        if (outcome === 'accepted') {
            setIsInstalled(true);
        }

        setShowPrompt(false);
        setDeferredPrompt(null);
    };

    const handleDismiss = () => {
        setShowPrompt(false);
        localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    };

    if (isInstalled || !showPrompt) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 100 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 100 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className="fixed bottom-4 left-4 right-4 z-50 md:left-auto md:right-4 md:max-w-sm"
            >
                <div className="relative overflow-hidden rounded-2xl border border-zinc-700/50 bg-zinc-900/95 p-4 shadow-2xl backdrop-blur-xl">
                    {/* Gradient accent */}
                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500" />

                    {/* Close button */}
                    <button
                        onClick={handleDismiss}
                        className="absolute right-3 top-3 rounded-full p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
                        aria-label="Закрыть"
                    >
                        <X className="h-4 w-4" />
                    </button>

                    <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                            <Smartphone className="h-6 w-6 text-white" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 pr-6">
                            <h3 className="font-semibold text-white">
                                Установить приложение
                            </h3>
                            <p className="mt-1 text-sm text-zinc-400">
                                Добавьте Digital Denis на главный экран для быстрого доступа
                            </p>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={handleDismiss}
                            className="flex-1 rounded-lg px-4 py-2.5 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
                        >
                            Не сейчас
                        </button>
                        <button
                            onClick={handleInstall}
                            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg transition-all hover:from-blue-600 hover:to-blue-700 hover:shadow-blue-500/25"
                        >
                            <Download className="h-4 w-4" />
                            Установить
                        </button>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
