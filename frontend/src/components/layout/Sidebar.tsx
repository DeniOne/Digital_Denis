/**
 * Digital Den — Sidebar Component
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUIStore, useAnalyticsStore } from '@/lib/store';

const navItems = [
    { href: '/', icon: '📊', label: 'Панель' },
    { href: '/chat', icon: '💬', label: 'Чат' },
    { href: '/schedule', icon: '📅', label: 'Расписание' },
    { href: '/memory', icon: '📁', label: 'Память' },
    { href: '/topics', icon: '🏷️', label: 'Темы' },
    { href: '/mindmap', icon: '🗺️', label: 'Карта мыслей' },
    { href: '/health', icon: '💚', label: 'Здоровье' },
];

export default function Sidebar() {
    const pathname = usePathname();
    const { sidebarOpen, toggleSidebar } = useUIStore();
    const { unreadCount } = useAnalyticsStore();

    return (
        <aside
            suppressHydrationWarning
            className={`fixed left-0 top-0 h-screen bg-zinc-900 border-r border-zinc-800 
        transition-all duration-300 z-40
        ${sidebarOpen ? 'w-56' : 'w-16'}`}
        >
            {/* Logo */}
            <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-800">
                {sidebarOpen && (
                    <span className="font-bold text-lg">🧠 Цифровой Дэн</span>
                )}
                {!sidebarOpen && <span className="text-xl">🧠</span>}
                <button
                    onClick={toggleSidebar}
                    className="p-1 hover:bg-zinc-800 rounded"
                >
                    {sidebarOpen ? '◀' : '▶'}
                </button>
            </div>

            {/* Navigation */}
            <nav className="p-2 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors
                ${isActive
                                    ? 'bg-blue-500/20 text-blue-400'
                                    : 'hover:bg-zinc-800 text-zinc-400 hover:text-white'}
              `}
                        >
                            <span className="text-lg">{item.icon}</span>
                            {sidebarOpen && (
                                <span className="font-medium">{item.label}</span>
                            )}
                            {/* Badge for Health */}
                            {item.href === '/health' && unreadCount > 0 && (
                                <span className="ml-auto bg-orange-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                                    {unreadCount}
                                </span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Divider */}
            <div className="absolute bottom-20 left-0 right-0 px-4">
                <div className="border-t border-zinc-800" />
            </div>

            {/* Settings */}
            <div className="absolute bottom-4 left-0 right-0 p-2">
                <Link
                    href="/settings"
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white"
                >
                    <span className="text-lg">⚙️</span>
                    {sidebarOpen && <span className="font-medium">Настройки</span>}
                </Link>
            </div>
        </aside>
    );
}
