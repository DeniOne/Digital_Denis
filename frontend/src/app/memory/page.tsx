"use client";

import { useState, useEffect } from "react";
import {
    Database,
    Search,
    Filter,
    Calendar,
    Tag,
    Trash2,
    ExternalLink,
    ChevronRight
} from "lucide-react";
import { memoryApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function MemoryPage() {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => {
        loadMemory();
    }, []);

    const loadMemory = async () => {
        setLoading(true);
        try {
            const data = await memoryApi.list();
            setItems(data.items);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const filteredItems = items.filter(item =>
        item.content.toLowerCase().includes(search.toLowerCase()) ||
        (item.summary && item.summary.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                        <Database className="text-indigo-500" size={28} />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Библиотека Памяти</h1>
                        <p className="text-zinc-500">Долгосрочное хранилище ваших решений и инсайтов.</p>
                    </div>
                </div>
            </div>

            {/* Toolbar */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1 group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Поиск по содержанию, типам или датам..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-[#0a0a0a] border border-white/5 rounded-2xl py-3 pl-12 pr-4 focus:outline-none focus:border-white/20 focus:ring-4 focus:ring-white/2 transition-all"
                    />
                </div>
                <button className="px-6 py-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center gap-2 font-medium">
                    <Filter size={18} />
                    <span>Фильтры</span>
                </button>
            </div>

            {/* Memory List */}
            <div className="space-y-4">
                {loading ? (
                    Array(3).fill(0).map((_, i) => (
                        <div key={i} className="h-32 rounded-3xl bg-white/5 animate-pulse" />
                    ))
                ) : filteredItems.length === 0 ? (
                    <div className="text-center py-20 border-2 border-dashed border-white/5 rounded-3xl">
                        <Database className="mx-auto text-zinc-700 mb-4" size={48} />
                        <h3 className="text-xl font-bold text-zinc-400">Ничего не найдено</h3>
                        <p className="text-zinc-600">Попробуйте изменить запрос или сохраните новое решение в чате.</p>
                    </div>
                ) : (
                    filteredItems.map((item) => (
                        <MemoryCard key={item.id} item={item} />
                    ))
                )}
            </div>
        </div>
    );
}

function MemoryCard({ item }: { item: any }) {
    const typeColors: any = {
        decision: "bg-blue-500/20 text-blue-400 border-blue-500/20",
        insight: "bg-purple-500/20 text-purple-400 border-purple-500/20",
        fact: "bg-zinc-800 text-zinc-400 border-white/10",
    };

    return (
        <div className="bg-[#0a0a0a]/50 border border-white/5 hover:border-white/10 rounded-3xl p-6 transition-all group cursor-pointer">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={cn("px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border", typeColors[item.item_type])}>
                        {item.item_type}
                    </div>
                    <div className="flex items-center gap-1.5 text-zinc-600 text-xs font-medium">
                        <Calendar size={12} />
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Unknown Date'}
                    </div>
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 rounded-lg hover:bg-red-500/10 text-zinc-600 hover:text-red-500 transition-all">
                        <Trash2 size={16} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-white/5 text-zinc-600 hover:text-white transition-all">
                        <ExternalLink size={16} />
                    </button>
                </div>
            </div>

            <h3 className="text-lg font-bold mb-2 group-hover:text-blue-400 transition-colors">
                {item.summary || item.content.split('\n')[0].replace('User: ', '')}
            </h3>

            <p className="text-zinc-500 text-sm line-clamp-2 mb-4 leading-relaxed">
                {item.content.replace('User: ', '').replace('Assistant: ', '')}
            </p>

            <div className="flex items-center gap-4 pt-4 border-t border-white/5">
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-600 uppercase">
                    <Tag size={12} />
                    Strategy, Business, MVP
                </div>
                <div className="ml-auto text-zinc-700 group-hover:text-white transition-colors">
                    <ChevronRight size={20} />
                </div>
            </div>
        </div>
    );
}
