/**
 * Digital Den — Mind Map Graph (Cytoscape.js)
 * ═══════════════════════════════════════════════════════════════════════════
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import type { GraphData, GraphNode, GraphEdge } from '@/lib/api';

interface MindMapGraphProps {
    data: GraphData;
    onNodeSelect?: (nodeId: string | null) => void;
    selectedNode?: string | null;
}

// Node styles by type
const nodeStyles = {
    decision: {
        shape: 'diamond',
        'background-color': '#22c55e',
    },
    insight: {
        shape: 'triangle',
        'background-color': '#eab308',
    },
    fact: {
        shape: 'rectangle',
        'background-color': '#3b82f6',
    },
    thought: {
        shape: 'ellipse',
        'background-color': '#8b5cf6',
    },
    topic: {
        shape: 'round-rectangle',
        'background-color': '#ec4899',
    },
};

// Edge styles by type
const edgeStyles = {
    depends_on: {
        'line-color': '#64748b',
        'target-arrow-color': '#64748b',
        'line-style': 'solid',
    },
    supports: {
        'line-color': '#22c55e',
        'target-arrow-color': '#22c55e',
        'line-style': 'solid',
    },
    contradicts: {
        'line-color': '#ef4444',
        'target-arrow-color': '#ef4444',
        'line-style': 'dashed',
    },
    related: {
        'line-color': '#6366f1',
        'target-arrow-color': '#6366f1',
        'line-style': 'dotted',
    },
};

export default function MindMapGraph({ data, onNodeSelect, selectedNode }: MindMapGraphProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<Core | null>(null);

    // Transform data to Cytoscape format
    const transformData = useCallback(() => {
        const nodes = data.nodes.map((node: GraphNode) => ({
            data: {
                id: node.id,
                label: node.label,
                type: node.type,
                size: node.size || 30,
                ...node.data,
            },
        }));

        const edges = data.edges.map((edge: GraphEdge) => ({
            data: {
                id: edge.id,
                source: edge.source,
                target: edge.target,
                type: edge.type,
                weight: edge.weight || 1,
            },
        }));

        return { nodes, edges };
    }, [data]);

    // Initialize Cytoscape
    useEffect(() => {
        if (!containerRef.current || !data.nodes.length) return;

        const elements = transformData();

        const cy = cytoscape({
            container: containerRef.current,
            elements: [...elements.nodes, ...elements.edges],

            layout: {
                name: 'cose',
                idealEdgeLength: 120,
                nodeOverlap: 20,
                refresh: 20,
                randomize: false,
                componentSpacing: 100,
                nodeRepulsion: () => 400000,
                edgeElasticity: () => 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0,
            },

            style: [
                // Base node style
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'font-size': 10,
                        'color': '#a1a1aa',
                        'text-outline-width': 2,
                        'text-outline-color': '#18181b',
                        'width': 'data(size)',
                        'height': 'data(size)',
                        'background-color': '#6366f1',
                    },
                },
                // Decision nodes
                {
                    selector: 'node[type="decision"]',
                    style: nodeStyles.decision as cytoscape.Css.Node,
                },
                // Insight nodes
                {
                    selector: 'node[type="insight"]',
                    style: nodeStyles.insight as cytoscape.Css.Node,
                },
                // Fact nodes
                {
                    selector: 'node[type="fact"]',
                    style: nodeStyles.fact as cytoscape.Css.Node,
                },
                // Topic nodes
                {
                    selector: 'node[type="topic"]',
                    style: nodeStyles.topic as cytoscape.Css.Node,
                },
                // Selected node
                {
                    selector: 'node:selected',
                    style: {
                        'border-width': 3,
                        'border-color': '#ffffff',
                        'border-opacity': 1,
                    },
                },
                // Base edge style
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#64748b',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#64748b',
                        'curve-style': 'bezier',
                        'opacity': 0.7,
                    },
                },
                // Edge types
                {
                    selector: 'edge[type="depends_on"]',
                    style: edgeStyles.depends_on as cytoscape.Css.Edge,
                },
                {
                    selector: 'edge[type="supports"]',
                    style: edgeStyles.supports as cytoscape.Css.Edge,
                },
                {
                    selector: 'edge[type="contradicts"]',
                    style: edgeStyles.contradicts as cytoscape.Css.Edge,
                },
                {
                    selector: 'edge[type="related"]',
                    style: edgeStyles.related as cytoscape.Css.Edge,
                },
            ],

            minZoom: 0.2,
            maxZoom: 3,
            wheelSensitivity: 0.3,
        });

        // Event handlers
        cy.on('tap', 'node', (evt) => {
            const node = evt.target as NodeSingular;
            onNodeSelect?.(node.id());
        });

        cy.on('tap', (evt) => {
            if (evt.target === cy) {
                onNodeSelect?.(null);
            }
        });

        cyRef.current = cy;

        return () => {
            cy.destroy();
        };
    }, [data, transformData, onNodeSelect]);

    // Handle selected node highlight
    useEffect(() => {
        if (!cyRef.current) return;

        cyRef.current.nodes().unselect();
        if (selectedNode) {
            cyRef.current.getElementById(selectedNode).select();
        }
    }, [selectedNode]);

    return (
        <div className="relative w-full h-full">
            <div ref={containerRef} className="w-full h-full bg-zinc-900 rounded-xl" />

            {/* Legend */}
            <div className="absolute bottom-4 left-4 bg-zinc-800/90 backdrop-blur rounded-lg px-4 py-3 text-xs">
                <div className="font-medium mb-2">Типы узлов</div>
                <div className="flex gap-4">
                    <span className="flex items-center gap-1">
                        <span className="w-3 h-3 bg-green-500 rotate-45" /> Решение
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-0 h-0 border-l-[6px] border-r-[6px] border-b-[10px] border-transparent border-b-yellow-500" /> Инсайт
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-3 h-3 bg-blue-500" /> Факт
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-3 h-3 bg-pink-500 rounded" /> Тема
                    </span>
                </div>
            </div>

            {/* Controls */}
            <div className="absolute top-4 right-4 flex gap-2">
                <button
                    onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
                    className="w-8 h-8 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center justify-center"
                >
                    +
                </button>
                <button
                    onClick={() => cyRef.current?.zoom(cyRef.current.zoom() / 1.2)}
                    className="w-8 h-8 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center justify-center"
                >
                    −
                </button>
                <button
                    onClick={() => cyRef.current?.fit()}
                    className="px-3 h-8 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
                >
                    Центр
                </button>
            </div>
        </div>
    );
}
