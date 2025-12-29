/**
 * Digital Denis — Mind Map Page
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useState } from 'react';
import { useGraph, useGraphStats } from '@/lib/hooks';
import { useGraphStore } from '@/lib/store';

export default function MindMapPage() {
    const { filters, setFilters, selectedNode, setSelectedNode } = useGraphStore();
    const { data: graphData, isLoading } = useGraph(filters);
    const { data: stats } = useGraphStats();

    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">🧠 Mind Map</h1>

                {/* Controls */}
                <div className="flex gap-4">
                    <select
                        value={filters.days}
                        onChange={(e) => setFilters({ days: parseInt(e.target.value) })}
                        className="bg-zinc-800 rounded-lg px-3 py-2 text-sm"
                    >
                        <option value={7}>7 days</option>
                        <option value={30}>30 days</option>
                        <option value={90}>90 days</option>
                    </select>

                    <select
                        value={filters.max_nodes}
                        onChange={(e) => setFilters({ max_nodes: parseInt(e.target.value) })}
                        className="bg-zinc-800 rounded-lg px-3 py-2 text-sm"
                    >
                        <option value={50}>50 nodes</option>
                        <option value={100}>100 nodes</option>
                        <option value={200}>200 nodes</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Graph Visualization */}
                <div className="lg:col-span-3 bg-zinc-900 rounded-xl p-4 min-h-[600px] relative">
                    {isLoading ? (
                        <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
                            Loading graph...
                        </div>
                    ) : graphData ? (
                        <div className="relative w-full h-full">
                            {/* Simple SVG visualization */}
                            <svg className="w-full h-full" viewBox="0 0 800 600">
                                {/* Edges */}
                                {graphData.edges.map((edge) => {
                                    const source = graphData.nodes.find(n => n.id === edge.source);
                                    const target = graphData.nodes.find(n => n.id === edge.target);
                                    if (!source || !target) return null;

                                    return (
                                        <line
                                            key={edge.id}
                                            x1={source.x || 400}
                                            y1={source.y || 300}
                                            x2={target.x || 400}
                                            y2={target.y || 300}
                                            stroke={edge.color || '#333'}
                                            strokeWidth={edge.weight || 1}
                                            opacity={0.5}
                                        />
                                    );
                                })}

                                {/* Nodes */}
                                {graphData.nodes.map((node) => (
                                    <g
                                        key={node.id}
                                        transform={`translate(${node.x || 400}, ${node.y || 300})`}
                                        className="cursor-pointer"
                                        onMouseEnter={() => setHoveredNode(node.id)}
                                        onMouseLeave={() => setHoveredNode(null)}
                                        onClick={() => setSelectedNode(node.id)}
                                    >
                                        <circle
                                            r={node.size || 8}
                                            fill={node.color || '#4f46e5'}
                                            stroke={selectedNode === node.id ? '#fff' : 'none'}
                                            strokeWidth={2}
                                        />
                                        {hoveredNode === node.id && (
                                            <text
                                                y={-12}
                                                textAnchor="middle"
                                                fill="white"
                                                fontSize="12"
                                            >
                                                {node.label}
                                            </text>
                                        )}
                                    </g>
                                ))}
                            </svg>

                            {/* Legend */}
                            <div className="absolute bottom-4 left-4 bg-zinc-800/80 rounded-lg px-3 py-2 text-xs">
                                <div className="flex gap-4">
                                    <span>🔵 Decision</span>
                                    <span>🟢 Insight</span>
                                    <span>🟡 Fact</span>
                                    <span>🟣 Topic</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
                            No graph data
                        </div>
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                    {/* Stats */}
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <h2 className="text-lg font-semibold mb-3">📊 Stats</h2>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Nodes</span>
                                <span>{graphData?.metadata?.total_nodes || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Edges</span>
                                <span>{graphData?.metadata?.total_edges || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Clusters</span>
                                <span>{graphData?.clusters?.length || 0}</span>
                            </div>
                        </div>
                    </div>

                    {/* Selected Node */}
                    {selectedNode && graphData && (
                        <div className="bg-zinc-900 rounded-xl p-4">
                            <h2 className="text-lg font-semibold mb-3">🎯 Selected</h2>
                            {(() => {
                                const node = graphData.nodes.find(n => n.id === selectedNode);
                                if (!node) return null;
                                return (
                                    <div className="space-y-2 text-sm">
                                        <p className="font-medium">{node.label}</p>
                                        <p className="text-zinc-400">Type: {node.type}</p>
                                    </div>
                                );
                            })()}
                        </div>
                    )}

                    {/* Clusters */}
                    {graphData?.clusters && graphData.clusters.length > 0 && (
                        <div className="bg-zinc-900 rounded-xl p-4">
                            <h2 className="text-lg font-semibold mb-3">🎨 Clusters</h2>
                            <div className="space-y-1 text-sm">
                                {graphData.clusters.map((cluster) => (
                                    <div key={cluster.id} className="flex justify-between">
                                        <span className="text-zinc-400">Cluster {cluster.id}</span>
                                        <span>{cluster.count} nodes</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
