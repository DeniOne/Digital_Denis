/**
 * Digital Denis — Topics Page
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useTopicTree, useTopicTrends } from '@/lib/hooks';
import { useTopicsStore } from '@/lib/store';
import type { Topic } from '@/lib/api';

function TopicNode({ topic, level = 0 }: { topic: Topic; level?: number }) {
    const { activeTopic, setActiveTopic, expandedTopics, toggleExpanded } = useTopicsStore();
    const isExpanded = expandedTopics.has(topic.id);
    const isActive = activeTopic?.id === topic.id;
    const hasChildren = topic.children && topic.children.length > 0;

    return (
        <div className="select-none">
            <div
                className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all
          ${isActive ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-zinc-800'}
        `}
                style={{ paddingLeft: `${level * 16 + 12}px` }}
                onClick={() => setActiveTopic(topic)}
            >
                {hasChildren && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            toggleExpanded(topic.id);
                        }}
                        className="w-4 h-4 flex items-center justify-center text-zinc-500"
                    >
                        {isExpanded ? '▼' : '▶'}
                    </button>
                )}
                {!hasChildren && <span className="w-4" />}

                <span className="flex-1">{topic.name}</span>

                {topic.item_count > 0 && (
                    <span className="text-xs text-zinc-500">{topic.item_count}</span>
                )}
            </div>

            {hasChildren && isExpanded && (
                <div>
                    {topic.children.map((child) => (
                        <TopicNode key={child.id} topic={child} level={level + 1} />
                    ))}
                </div>
            )}
        </div>
    );
}

function TrendBadge({ change }: { change: number }) {
    if (change > 10) return <span className="text-green-400">↑ +{change.toFixed(0)}%</span>;
    if (change < -10) return <span className="text-red-400">↓ {change.toFixed(0)}%</span>;
    return <span className="text-zinc-500">—</span>;
}

export default function TopicsPage() {
    const { data: topicTree, isLoading: treeLoading } = useTopicTree();
    const { data: trends, isLoading: trendsLoading } = useTopicTrends();
    const { activeTopic } = useTopicsStore();

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6">
            <h1 className="text-2xl font-bold mb-6">🏷️ Topics Explorer</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Topic Tree */}
                <div className="lg:col-span-2 bg-zinc-900 rounded-xl p-4">
                    <h2 className="text-lg font-semibold mb-4">Topic Tree</h2>

                    {treeLoading ? (
                        <div className="text-zinc-500">Loading...</div>
                    ) : (
                        <div className="space-y-1">
                            {topicTree?.map((topic: Topic) => (
                                <TopicNode key={topic.id} topic={topic} />
                            ))}
                        </div>
                    )}
                </div>

                {/* Trends Sidebar */}
                <div className="space-y-4">
                    {/* Active Topic Details */}
                    {activeTopic && (
                        <div className="bg-zinc-900 rounded-xl p-4">
                            <h2 className="text-lg font-semibold mb-3">{activeTopic.name}</h2>
                            <div className="text-sm text-zinc-400 space-y-1">
                                <p>Level: {activeTopic.level}</p>
                                <p>Items: {activeTopic.item_count}</p>
                            </div>
                        </div>
                    )}

                    {/* Trends */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-4">📈 Trends (7d)</h2>

                        {trendsLoading ? (
                            <div className="text-zinc-500">Loading...</div>
                        ) : (
                            <div className="space-y-2">
                                {trends?.slice(0, 10).map((trend: { topic_id: string; topic_name: string; change_percent: number }) => (
                                    <div key={trend.topic_id} className="flex justify-between items-center">
                                        <span className="text-sm">{trend.topic_name}</span>
                                        <TrendBadge change={trend.change_percent} />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
