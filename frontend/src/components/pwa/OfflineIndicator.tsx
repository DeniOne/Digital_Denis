'use client';

import { useState, useEffect } from 'react';
import { WifiOff, Wifi } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { syncManager } from '@/lib/sync/manager';

export function OfflineIndicator() {
    const [isOnline, setIsOnline] = useState(true);
    const [showRestored, setShowRestored] = useState(false);

    useEffect(() => {
        // Initial state
        if (setIsOnline) {
            // Safe update
            const current = syncManager.online;
            setIsOnline(prev => prev !== current ? current : prev);
        }

        // Subscribe to changes
        const unsubscribe = syncManager.subscribe((online) => {
            if (!isOnline && online) {
                // Connection restored
                setShowRestored(true);
                setTimeout(() => setShowRestored(false), 3000);
            }
            setIsOnline(online);
        });

        return unsubscribe;
    }, [isOnline]);

    if (isOnline && !showRestored) return null;

    return (
        <AnimatePresence>
            {!isOnline && (
                <motion.div
                    key="offline"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-center bg-red-500/90 py-1.5 text-xs font-medium text-white backdrop-blur-sm"
                >
                    <WifiOff className="mr-2 h-3 w-3" />
                    <span>Нет подключения к интернету. Изменения сохранены локально.</span>
                </motion.div>
            )}

            {showRestored && (
                <motion.div
                    key="restored"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-center bg-green-500/90 py-1.5 text-xs font-medium text-white backdrop-blur-sm"
                >
                    <Wifi className="mr-2 h-3 w-3" />
                    <span>Подключение восстановлено. Синхронизация...</span>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
