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
import { cn } from '@/lib/utils';

import type { TargetTopology, TopologyNode } from '../services/executionApi';
import { layoutWithDagre } from '../utils/graphLayout';

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
      className={cn(
        'flex items-center gap-2 min-w-[148px] max-w-[180px] px-2.5 py-2 rounded-[10px] border-[1.5px] border-[#475569] bg-gradient-to-b from-[#0f172a] to-[#0b1220] shadow-[0_2px_8px_rgba(0,0,0,0.35)] relative font-[Inter,system-ui,sans-serif]',
        selected && 'shadow-[0_0_0_2px_rgba(34,197,94,0.45),0_4px_14px_rgba(0,0,0,0.4)] bg-[#111827]',
        data.isActiveAttack && 'animate-[attackPulse_1.4s_ease-in-out_infinite]',
      )}
      style={{ borderColor: data.color, ['--atm-color' as string]: data.color }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-1.5 !h-1.5 !bg-[#334155] !border !border-[#64748b] opacity-70"
      />
      {data.isActiveAttack && (
        <span className="absolute -top-2 -right-1.5 text-[11px] leading-none [filter:drop-shadow(0_0_4px_rgba(244,114,182,0.7))]" title="Active AI attack">
          🤖
        </span>
      )}
      <span className="text-sm leading-none shrink-0" aria-hidden>
        {data.icon}
      </span>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[9px] uppercase tracking-[0.04em] text-[var(--atm-color,#94a3b8)] font-semibold">
          {data.assetType}
        </span>
        <span className="text-[11px] text-[#e2e8f0] whitespace-nowrap overflow-hidden text-ellipsis font-['Fira_Code',ui-monospace,monospace]" title={data.label}>
          {data.label.length > 22 ? `${data.label.slice(0, 20)}…` : data.label}
        </span>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-1.5 !h-1.5 !bg-[#334155] !border !border-[#64748b] opacity-70"
      />
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
      className="bg-[#0b1220]"
    >
      <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#1e293b" />
      <Controls
        showInteractive={false}
        className="!bg-[#0f172a] !border !border-[#1e293b] !rounded-lg !shadow-none [&_button]:!bg-[#0f172a] [&_button]:!border-b-[#1e293b] [&_button]:!fill-[#94a3b8] [&_button:hover]:!bg-[#1e293b]"
      />
      <MiniMap
        className="!bg-[#0f172a] !border !border-[#1e293b] !rounded-lg"
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
    return <div className="px-3 py-7 text-center text-[#64748b] text-[0.78rem]">Select a target-bound thread to view topology</div>;
  }

  if (topology.nodes.length === 0) {
    return <div className="px-3 py-7 text-center text-[#64748b] text-[0.78rem]">No assets for {topology.target_name}</div>;
  }

  return (
    <>
      <style>{`@keyframes attackPulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(244, 114, 182, 0.15); } 50% { box-shadow: 0 0 0 6px rgba(244, 114, 182, 0.28); } }`}</style>
      <div
        className="bg-[#0b1220] border border-[#1e293b] rounded-[10px] overflow-hidden flex flex-col [&_.react-flow__edge-textbg]:fill-[#0b1220] [&_.react-flow__edge-text]:fill-[#64748b]"
        data-testid="asset-topology-map"
      >
      <div className="flex justify-between items-center px-3 py-2 border-b border-[#1e293b] gap-2 shrink-0">
        <span className="text-[0.75rem] font-semibold text-[#e2e8f0]">Topology · {topology.target_name}</span>
        <span className="text-[0.68rem] text-[#64748b]">
          {topology.nodes.length} nodes · {topology.edges.length} edges
          {topology.active_attacks?.length
            ? ` · 🤖 ${topology.active_attacks.length} active`
            : ''}
        </span>
      </div>
      <div className="w-full h-[360px] min-h-[280px]">
        <ReactFlowProvider>
          <TopologyFlowInner
            topology={topology}
            onSelectNode={onSelectNode}
            selectedNodeId={selectedNodeId}
          />
        </ReactFlowProvider>
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-2 px-3 py-1.5 pb-2.5 border-t border-[#1e293b] shrink-0">
        {Object.entries(TYPE_COLOR).map(([type, color]) => (
          <span key={type} className="inline-flex items-center gap-1 text-[0.65rem] text-[#64748b] capitalize">
            <i className="w-2 h-2 rounded-full inline-block" style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </>
  );
}

export default AssetTopologyMap;
