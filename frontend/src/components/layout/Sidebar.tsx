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

    // Close on mobile navigation
    const handleLinkClick = () => {
        if (window.innerWidth < 768 && sidebarOpen) {
            toggleSidebar();
        }
    };

    return (
        <>
            {/* Mobile Backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
                    onClick={toggleSidebar}
                />
            )}

            <aside
                suppressHydrationWarning
                className={`fixed left-0 top-0 h-screen bg-zinc-900 border-r border-zinc-800 
        transition-all duration-300 z-50
        ${/* Mobile: Drawer logic */ ''}
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} w-64
        ${/* Desktop: Mini/Full logic */ ''}
        md:translate-x-0
        ${sidebarOpen ? 'md:w-56' : 'md:w-16'}`}
            >
                {/* Logo */}
                <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-800">
                    {/* Desktop: Show text if open */}
                    <span className={`font-bold text-lg transition-opacity duration-200
                        ${sidebarOpen ? 'opacity-100' : 'opacity-0 hidden md:block md:opacity-0'} 
                        ${sidebarOpen ? 'md:block' : 'md:hidden'}
                    `}>
                        {sidebarOpen && '🧠 Цифровой Дэн'}
                    </span>

                    {/* Mobile: Always show text */}
                    <span className="font-bold text-lg md:hidden">🧠 Цифровой Дэн</span>

                    {/* Desktop: Mini logo when closed */}
                    {!sidebarOpen && <span className="text-xl hidden md:block">🧠</span>}

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
                                onClick={handleLinkClick}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors
                ${isActive
                                        ? 'bg-blue-500/20 text-blue-400'
                                        : 'hover:bg-zinc-800 text-zinc-400 hover:text-white'}
              `}
                            >
                                <span className="text-lg min-w-[24px] text-center">{item.icon}</span>

                                {/* Label: Show on mobile (drawer open) OR desktop (if expanded) */}
                                <span className={`font-medium whitespace-nowrap transition-all duration-200
                                    ${sidebarOpen ? 'opacity-100' : 'md:opacity-0 md:w-0 md:hidden'}
                                `}>
                                    {item.label}
                                </span>

                                {/* Badge for Health */}
                                {item.href === '/health' && unreadCount > 0 && (
                                    <span className={`ml-auto bg-orange-500 text-white text-xs px-1.5 py-0.5 rounded-full
                                        ${!sidebarOpen && 'md:hidden'}
                                    `}>
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
                        onClick={handleLinkClick}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white"
                    >
                        <span className="text-lg min-w-[24px] text-center">⚙️</span>
                        <span className={`font-medium whitespace-nowrap transition-all duration-200
                             ${sidebarOpen ? 'opacity-100' : 'md:opacity-0 md:w-0 md:hidden'}
                        `}>
                            Настройки
                        </span>
                    </Link>
                </div>
            </aside>
        </>
    );
}
