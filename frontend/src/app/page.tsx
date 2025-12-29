/**
 * Digital Denis — Dashboard Page (Main)
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import Link from 'next/link';
import { useMemories, useTopicTrends, useAnomalies, useCognitiveHealth } from '@/lib/hooks';
import type { MemoryItem, Anomaly, TopicTrend } from '@/lib/api';

function StatCard({ icon, value, label, trend }: { icon: string; value: string | number; label: string; trend?: string }) {
  return (
    <div className="bg-zinc-900 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <span className={`text-xs px-1.5 py-0.5 rounded ${trend.startsWith('+') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
            {trend}
          </span>
        )}
      </div>
      <div className="text-sm text-zinc-400">{label}</div>
    </div>
  );
}

function MemoryCard({ item }: { item: MemoryItem }) {
  const typeIcons: Record<string, string> = {
    decision: '✅',
    insight: '💎',
    fact: '📌',
    thought: '💭',
  };

  return (
    <div className="bg-zinc-800 rounded-lg p-4 hover:bg-zinc-750 transition-colors">
      <div className="flex items-start gap-3">
        <span className="text-lg">{typeIcons[item.item_type] || '📄'}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium line-clamp-2">{item.content}</p>
          <div className="flex items-center gap-2 mt-2 text-xs text-zinc-500">
            <span>{new Date(item.created_at).toLocaleDateString()}</span>
            {item.confidence && (
              <span className="bg-zinc-700 px-1.5 py-0.5 rounded">
                {Math.round(item.confidence * 100)}%
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AnomalyAlert({ anomaly }: { anomaly: Anomaly }) {
  const severityColors: Record<string, string> = {
    low: 'border-green-500/30 bg-green-500/5',
    medium: 'border-yellow-500/30 bg-yellow-500/5',
    high: 'border-orange-500/30 bg-orange-500/5',
    critical: 'border-red-500/30 bg-red-500/5',
  };

  const severityIcons: Record<string, string> = {
    low: '🟢',
    medium: '🟡',
    high: '🟠',
    critical: '🔴',
  };

  return (
    <div className={`border rounded-xl p-4 ${severityColors[anomaly.severity] || severityColors.medium}`}>
      <div className="flex items-start gap-3">
        <span className="text-lg">{severityIcons[anomaly.severity]}</span>
        <div className="flex-1">
          <h4 className="font-medium">{anomaly.title}</h4>
          <p className="text-sm text-zinc-400 mt-1">{anomaly.interpretation}</p>
          <div className="flex gap-2 mt-3">
            <Link
              href="/health"
              className="text-xs px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors"
            >
              View Details
            </Link>
            <button className="text-xs px-3 py-1.5 text-zinc-500 hover:text-white transition-colors">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: health } = useCognitiveHealth();
  const { data: memoriesData } = useMemories({ limit: 5, offset: 0, item_type: 'decision' });
  const { data: insightsData } = useMemories({ limit: 5, offset: 0, item_type: 'insight' });
  const { data: anomalies } = useAnomalies('new');
  const { data: trends } = useTopicTrends();

  const decisions = memoriesData?.items || [];
  const insights = insightsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold">Welcome back, Denis</h1>
        <p className="text-zinc-400 mt-1">Here&apos;s your cognitive overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon="🧠"
          value={health?.total_memories || 0}
          label="Total Memories"
        />
        <StatCard
          icon="✅"
          value={decisions.length}
          label="Decisions (recent)"
        />
        <StatCard
          icon="🏷️"
          value={health?.active_topics || 0}
          label="Active Topics"
        />
        <StatCard
          icon="💚"
          value={health?.overall_score ? `${Math.round(health.overall_score * 100)}%` : '--'}
          label="Health Score"
        />
      </div>

      {/* Active Topics */}
      {trends && trends.length > 0 && (
        <div className="bg-zinc-900 rounded-xl p-4">
          <h3 className="font-semibold mb-3">Active Topics</h3>
          <div className="flex flex-wrap gap-2">
            {trends.slice(0, 6).map((trend: TopicTrend) => (
              <Link
                key={trend.topic_id}
                href={`/topics?id=${trend.topic_id}`}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${trend.change_percent > 20
                    ? 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30'
                    : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                  }`}
              >
                {trend.topic_name}
                {trend.change_percent > 20 && ' 🔥'}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Decisions */}
        <div className="bg-zinc-900 rounded-xl p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">📈 Recent Decisions</h3>
            <Link href="/memory?type=decision" className="text-sm text-blue-400 hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {decisions.length > 0 ? (
              decisions.map((item: MemoryItem) => (
                <MemoryCard key={item.id} item={item} />
              ))
            ) : (
              <p className="text-zinc-500 text-sm">No recent decisions</p>
            )}
          </div>
        </div>

        {/* Recent Insights */}
        <div className="bg-zinc-900 rounded-xl p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">💡 Recent Insights</h3>
            <Link href="/memory?type=insight" className="text-sm text-blue-400 hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {insights.length > 0 ? (
              insights.map((item: MemoryItem) => (
                <MemoryCard key={item.id} item={item} />
              ))
            ) : (
              <p className="text-zinc-500 text-sm">No recent insights</p>
            )}
          </div>
        </div>
      </div>

      {/* Anomaly Alerts */}
      {anomalies && anomalies.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold">⚠️ Anomaly Alerts</h3>
          {anomalies.slice(0, 2).map((anomaly: Anomaly) => (
            <AnomalyAlert key={anomaly.id} anomaly={anomaly} />
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link
          href="/chat"
          className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-xl p-4 hover:border-blue-400/50 transition-colors"
        >
          <span className="text-2xl">💬</span>
          <p className="font-medium mt-2">Start Chat</p>
          <p className="text-xs text-zinc-400">Talk to Digital Denis</p>
        </Link>

        <Link
          href="/memory"
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
        >
          <span className="text-2xl">🔍</span>
          <p className="font-medium mt-2">Search Memory</p>
          <p className="text-xs text-zinc-400">Find past thoughts</p>
        </Link>

        <Link
          href="/mindmap"
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
        >
          <span className="text-2xl">🗺️</span>
          <p className="font-medium mt-2">Mind Map</p>
          <p className="text-xs text-zinc-400">Visualize connections</p>
        </Link>

        <Link
          href="/health"
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
        >
          <span className="text-2xl">📊</span>
          <p className="font-medium mt-2">Health Report</p>
          <p className="text-xs text-zinc-400">Check cognitive health</p>
        </Link>
      </div>
    </div>
  );
}
