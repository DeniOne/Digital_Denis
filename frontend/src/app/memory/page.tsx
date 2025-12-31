"use client";

import { useState } from "react";
import { useMemories } from "@/lib/hooks";
import { MemoryItem } from "@/lib/api";

const memoryTypes = [
    { value: 'all', label: 'Все типы' },
    { value: 'decision', label: 'Решения' },
    { value: 'insight', label: 'Инсайты' },
    { value: 'fact', label: 'Факты' },
    { value: 'thought', label: 'Мысли' },
];

export default function MemoryExplorer() {
    const [search, setSearch] = useState('');
    const [type, setType] = useState('all');
    const [topic, setTopic] = useState<string | undefined>();

    const { data, isLoading } = useMemories({
        item_type: type === 'all' ? undefined : type,
        topic_id: topic,
    });

    // API returns { items: [...], total: number }
    const memories = data?.items;

    const filteredMemories = memories?.filter((m: MemoryItem) =>
        m.content.toLowerCase().includes(search.toLowerCase())
    );

    const getTypeLabel = (itemType: string) => {
        switch (itemType) {
            case 'decision': return 'Решение';
            case 'insight': return 'Инсайт';
            case 'fact': return 'Факт';
            default: return 'Мысль';
        }
    };

    const getTypeStyle = (itemType: string) => {
        switch (itemType) {
            case 'decision': return 'bg-green-500/10 text-green-400';
            case 'insight': return 'bg-blue-500/10 text-blue-400';
            default: return 'bg-zinc-500/10 text-zinc-400';
        }
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold">📁 Проводник памяти</h1>
                    <p className="text-zinc-400 mt-1">Исследуйте и фильтруйте ваши цифровые воспоминания</p>
                </div>

                <div className="flex flex-wrap gap-3">
                    {/* Search */}
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">🔍</span>
                        <input
                            type="text"
                            placeholder="Поиск воспоминаний..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        />
                    </div>

                    {/* Type Filter */}
                    <select
                        value={type}
                        onChange={(e) => setType(e.target.value)}
                        className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    >
                        {memoryTypes.map((t) => (
                            <option key={t.value} value={t.value}>
                                {t.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="h-48 bg-zinc-900/50 rounded-xl animate-pulse" />
                    ))}
                </div>
            ) : filteredMemories && filteredMemories.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredMemories.map((memory: MemoryItem) => (
                        <div
                            key={memory.id}
                            className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-colors group"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <span className={`text-xs px-2 py-1 rounded-md ${getTypeStyle(memory.item_type)}`}>
                                    {getTypeLabel(memory.item_type)}
                                </span>
                                <span className="text-xs text-zinc-500">
                                    {new Date(memory.created_at).toLocaleDateString()}
                                </span>
                            </div>

                            <p className="text-zinc-200 line-clamp-3 mb-4 leading-relaxed">
                                {memory.content}
                            </p>

                            <div className="flex flex-wrap gap-2 mt-auto">
                                {memory.topics?.map((topic) => (
                                    <span
                                        key={topic.id}
                                        className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded"
                                    >
                                        #{topic.name}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
                    <span className="text-4xl mb-4">🏜️</span>
                    <p>Воспоминаний не найдено</p>
                    <button
                        onClick={() => { setType('all'); setSearch(''); }}
                        className="mt-4 text-blue-400 hover:underline text-sm"
                    >
                        Сбросить фильтры
                    </button>
                </div>
            )}
        </div>
    );
}
