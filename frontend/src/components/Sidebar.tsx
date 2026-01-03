"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    MessageSquare,
    Database,
    LayoutDashboard,
    Settings,
    BrainCircuit,
    PlusCircle,
    Calendar
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Chat", href: "/chat", icon: MessageSquare },
    { name: "Расписание", href: "/schedule", icon: Calendar },
    { name: "Memory", href: "/memory", icon: Database },
    { name: "Analytics", href: "/analytics", icon: BrainCircuit },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="hidden lg:flex flex-col w-64 bg-[#0a0a0a]/80 backdrop-blur-xl border-r border-white/5 h-full">
            <div className="p-6">
                <div className="flex items-center gap-3 text-white font-bold text-xl tracking-tight">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <BrainCircuit size={20} />
                    </div>
                    <span>Digital Den</span>
                </div>
            </div>

            <nav className="flex-1 px-4 space-y-1 mt-4">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group",
                                isActive
                                    ? "bg-white/10 text-white shadow-inner"
                                    : "text-zinc-500 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <item.icon size={20} className={cn(
                                "transition-colors",
                                isActive ? "text-blue-500" : "group-hover:text-blue-400"
                            )} />
                            <span className="font-medium">{item.name}</span>
                            {isActive && (
                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 mt-auto">
                <Link href="/chat" className="block">
                    <button className="flex items-center gap-3 w-full px-3 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold shadow-lg shadow-blue-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all">
                        <PlusCircle size={20} />
                        <span>New Insight</span>
                    </button>
                </Link>

                <div className="mt-4 pt-4 border-t border-white/5 px-2">
                    <Link
                        href="/settings"
                        className="flex items-center gap-3 text-zinc-500 hover:text-white transition-colors py-2"
                    >
                        <Settings size={20} />
                        <span className="font-medium">Settings</span>
                    </Link>
                </div>
            </div>
        </aside>
    );
}
