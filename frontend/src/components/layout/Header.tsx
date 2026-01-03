/**
 * Digital Den — Header Component
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { usePathname } from 'next/navigation';
import { useUIStore, useAnalyticsStore, useSessionStore } from '@/lib/store';

const pageTitles: Record<string, string> = {
    '/': 'Панель управления',
    '/chat': 'Чат с Дэном',
    '/schedule': 'Расписание и задачи',
    '/memory': 'Проводник памяти',
    '/topics': 'Темы и смыслы',
    '/mindmap': 'Карта мыслей',
    '/health': 'Когнитивное здоровье',
    '/settings': 'Настройки',
};

export default function Header() {
    const pathname = usePathname();
    const { sidebarOpen, toggleCommandPalette } = useUIStore();
    const { unreadCount } = useAnalyticsStore();
    const { sessionId } = useSessionStore();

    const title = pageTitles[pathname] || 'Digital Den';

    return (
        <header
            className={`fixed top-0 right-0 h-16 bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-800 z-30
        transition-all duration-300
        ${sidebarOpen ? 'left-56' : 'left-16'}`}
        >
            <div className="h-full flex items-center justify-between px-6">
                {/* Page Title */}
                <div className="flex items-center gap-4">
                    <h1 className="text-xl font-semibold">{title}</h1>

                    {/* Session indicator */}
                    {sessionId && (
                        <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-1 rounded">
                            Сессия активна
                        </span>
                    )}
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-4">
                    {/* Search */}
                    <button
                        onClick={toggleCommandPalette}
                        className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 rounded-lg text-zinc-400 hover:text-white text-sm"
                    >
                        <span>🔍</span>
                        <span className="hidden sm:inline">Поиск...</span>
                        <kbd className="hidden sm:inline ml-2 text-xs text-zinc-500 bg-zinc-700 px-1.5 py-0.5 rounded">
                            ⌘K
                        </kbd>
                    </button>

                    {/* Notifications */}
                    <button className="relative p-2 hover:bg-zinc-800 rounded-lg">
                        <span className="text-lg">🔔</span>
                        {unreadCount > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 text-white text-xs rounded-full flex items-center justify-center">
                                {unreadCount > 9 ? '9+' : unreadCount}
                            </span>
                        )}
                    </button>

                    {/* User Menu */}
                    <button className="flex items-center gap-2 px-3 py-1.5 hover:bg-zinc-800 rounded-lg">
                        <span className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                            D
                        </span>
                        <span className="hidden sm:inline text-sm">Den</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
