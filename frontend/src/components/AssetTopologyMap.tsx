import { useCallback, useEffect, useMemo, memo } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  MarkerType,
  useNodesState,
  useEdgesState,
  useReactFlow,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeProps,
  type NodeMouseHandler,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import type { TargetTopology, TopologyNode } from '../services/executionApi';
import { layoutWithDagre } from '../utils/graphLayout';
import './AssetTopologyMap.css';

interface AssetTopologyMapProps {
  topology: TargetTopology | null;
  onSelectNode?: (node: TopologyNode) => void;
  selectedNodeId?: string | null;
}

const TYPE_COLOR: Record<string, string> = {
  target: '#a78bfa',
  seed: '#60a5fa',
  subdomain: '#34d399',
  ip: '#fbbf24',
  url: '#94a3b8',
  vulnerability: '#ef4444',
  port: '#f59e0b',
  endpoint: '#8b5cf6',
  dnsrecord: '#06b6d4',
  techstack: '#10b981',
  attackvector: '#ec4899',
};

const TYPE_ICON: Record<string, string> = {
  target: '🎯',
  seed: '🌱',
  subdomain: '🌐',
  ip: '🖥',
  url: '🔗',
  vulnerability: '⚠️',
  port: '🔌',
  endpoint: '🔗',
  dnsrecord: '📋',
  techstack: '📊',
  attackvector: '🎯',
};

/** Prefer rank for similar asset layers when dagre lays out. */
const TYPE_RANK: Record<string, number> = {
  target: 0,
  seed: 1,
  subdomain: 1,
  ip: 2,
  port: 3,
  url: 3,
  endpoint: 3,
  dnsrecord: 2,
  techstack: 3,
  vulnerability: 4,
  attackvector: 4,
};

type AssetNodeData = {
  label: string;
  assetType: string;
  color: string;
  icon: string;
  isActiveAttack: boolean;
  topologyNode: TopologyNode;
};

type AssetFlowNode = Node<AssetNodeData, 'asset'>;
type AssetFlowEdge = Edge<{ edgeType?: string }>;

const AssetNode = memo(function AssetNode({ data, selected }: NodeProps<AssetFlowNode>) {
  return (
    <div
      className={[
        'atm-rf-node',
        selected ? 'atm-rf-node--selected' : '',
        data.isActiveAttack ? 'atm-rf-node--attack' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      style={{ borderColor: data.color, ['--atm-color' as string]: data.color }}
    >
      <Handle type="target" position={Position.Top} className="atm-rf-handle" />
      {data.isActiveAttack && <span className="atm-rf-attack-badge" title="Active AI attack">🤖</span>}
      <span className="atm-rf-icon" aria-hidden>
        {data.icon}
      </span>
      <div className="atm-rf-body">
        <span className="atm-rf-type">{data.assetType}</span>
        <span className="atm-rf-label" title={data.label}>
          {data.label.length > 22 ? `${data.label.slice(0, 20)}…` : data.label}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} className="atm-rf-handle" />
    </div>
  );
});

const nodeTypes = { asset: AssetNode };

function buildGraph(topology: TargetTopology): {
  nodes: AssetFlowNode[];
  edges: AssetFlowEdge[];
} {
  // Sort by preferred rank so dagre tends to stack layers predictably
  const sorted = [...topology.nodes].sort(
    (a, b) => (TYPE_RANK[a.type] ?? 2) - (TYPE_RANK[b.type] ?? 2),
  );

  const nodes: AssetFlowNode[] = sorted.map((n) => {
    const color = TYPE_COLOR[n.type] || '#94a3b8';
    return {
      id: n.id,
      type: 'asset',
      position: { x: 0, y: 0 },
      data: {
        label: n.label,
        assetType: n.type,
        color,
        icon: TYPE_ICON[n.type] || '●',
        isActiveAttack: Boolean(n.is_active_attack),
        topologyNode: n,
      },
      width: 168,
      height: 52,
    };
  });

  const edges: AssetFlowEdge[] = topology.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    label: e.edge_type || undefined,
    markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: '#475569' },
    data: { edgeType: e.edge_type },
    style: { stroke: '#334155', strokeWidth: 1.4 },
    labelStyle: { fill: '#64748b', fontSize: 9 },
    labelBgStyle: { fill: '#0b1220', fillOpacity: 0.85 },
    labelBgPadding: [4, 2] as [number, number],
  }));

  const laidOut = layoutWithDagre(nodes, edges, {
    direction: 'TB',
    nodeWidth: 168,
    nodeHeight: 52,
    nodesep: 28,
    ranksep: 70,
  });

  return { nodes: laidOut, edges };
}

function TopologyFlowInner({
  topology,
  onSelectNode,
  selectedNodeId,
}: {
  topology: TargetTopology;
  onSelectNode?: (node: TopologyNode) => void;
  selectedNodeId?: string | null;
}) {
  const { fitView } = useReactFlow();
  const built = useMemo(() => buildGraph(topology), [topology]);
  const [nodes, setNodes, onNodesChange] = useNodesState(built.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(built.edges);

  // Rebuild when topology data changes
  useEffect(() => {
    setNodes(built.nodes);
    setEdges(built.edges);
    // Fit after paint so measured sizes settle
    const t = requestAnimationFrame(() => {
      fitView({ padding: 0.15, duration: 200 });
    });
    return () => cancelAnimationFrame(t);
  }, [built, setNodes, setEdges, fitView]);

  // Mirror external selection into RF selected flags
  useEffect(() => {
    setNodes((prev) =>
      prev.map((n) => ({
        ...n,
        selected: selectedNodeId ? n.id === selectedNodeId : false,
      })),
    );
  }, [selectedNodeId, setNodes]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_evt, node) => {
      const data = node.data as AssetNodeData;
      if (data?.topologyNode) onSelectNode?.(data.topologyNode);
    },
    [onSelectNode],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.2}
      maxZoom={1.8}
      proOptions={{ hideAttribution: true }}
      nodesConnectable={false}
      edgesReconnectable={false}
      elementsSelectable
      panOnScroll
      zoomOnScroll
      colorMode="dark"
      className="atm-rf-canvas"
    >
      <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#1e293b" />
      <Controls showInteractive={false} className="atm-rf-controls" />
      <MiniMap
        className="atm-rf-minimap"
        nodeColor={(n) => (n.data as AssetNodeData)?.color || '#475569'}
        maskColor="rgba(15, 23, 42, 0.75)"
        pannable
        zoomable
      />
    </ReactFlow>
  );
}

export function AssetTopologyMap({ topology, onSelectNode, selectedNodeId }: AssetTopologyMapProps) {
  if (!topology) {
    return <div className="atm-empty">Select a target-bound thread to view topology</div>;
  }

  if (topology.nodes.length === 0) {
    return <div className="atm-empty">No assets for {topology.target_name}</div>;
  }

  return (
    <div className="asset-topology-map" data-testid="asset-topology-map">
      <div className="atm-header">
        <span className="atm-title">Topology · {topology.target_name}</span>
        <span className="atm-stats">
          {topology.nodes.length} nodes · {topology.edges.length} edges
          {topology.active_attacks?.length
            ? ` · 🤖 ${topology.active_attacks.length} active`
            : ''}
        </span>
      </div>
      <div className="atm-rf-viewport">
        <ReactFlowProvider>
          <TopologyFlowInner
            topology={topology}
            onSelectNode={onSelectNode}
            selectedNodeId={selectedNodeId}
          />
        </ReactFlowProvider>
      </div>
      <div className="atm-legend">
        {Object.entries(TYPE_COLOR).map(([type, color]) => (
          <span key={type} className="atm-legend-item">
            <i style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}

export default AssetTopologyMap;
