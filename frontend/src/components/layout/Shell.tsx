/**
 * Digital Den — Shell Layout
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import { useUIStore } from '@/lib/store';

interface ShellProps {
    children: ReactNode;
}

export default function Shell({ children }: ShellProps) {
    const { sidebarOpen } = useUIStore();

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            <Sidebar />
            <Header />

            {/* Main Content */}
            <main
                className={`pt-16 min-h-screen transition-all duration-300
          ${sidebarOpen ? 'md:pl-56' : 'md:pl-16'}`}
            >
                <div className="p-4 md:p-6">
                    {children}
                </div>
            </main>
        </div>
    );
}
