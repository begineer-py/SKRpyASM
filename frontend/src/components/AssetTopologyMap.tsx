import { useCallback, useEffect, useMemo, memo, useState } from 'react';
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
import { Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

import type { AssetMapEdge, AssetMapGraph, AssetMapNode } from '../features/target/assetMap/types';
import { layoutWithDagre } from '../utils/graphLayout';

interface AssetTopologyMapProps {
  graph: AssetMapGraph | null;
  onSelectNode?: (node: AssetMapNode) => void;
  selectedNodeId?: string | null;
}

const TYPE_TONE = {
  attackvector: 'purple',
  dnsrecord: 'cyan',
  endpoint: 'blue',
  ip: 'amber',
  port: 'amber',
  seed: 'blue',
  subdomain: 'green',
  target: 'purple',
  techstack: 'green',
  url: 'cyan',
  vulnerability: 'red',
} as const;

type TopologyTone = (typeof TYPE_TONE)[keyof typeof TYPE_TONE];

const TONE_VARIABLE = {
  amber: 'var(--amber)',
  blue: 'var(--blue)',
  cyan: 'var(--cyan)',
  green: 'var(--green)',
  purple: 'var(--purple)',
  red: 'var(--red)',
} as const satisfies Record<TopologyTone, string>;

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
  tone: TopologyTone;
  isActiveAttack: boolean;
  assetNode: AssetMapNode;
};

type AssetFlowNode = Node<AssetNodeData, 'asset'>;
type AssetFlowEdge = Edge<{ edgeType?: string }>;

const AssetNode = memo(function AssetNode({ data, selected }: NodeProps<AssetFlowNode>) {
  return (
    <div
      className={cn(
        'asset-topology-node',
        `asset-topology-node--${data.tone}`,
        selected && 'asset-topology-node--selected',
        data.isActiveAttack && 'asset-topology-node--active',
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="asset-topology-node__handle"
      />
      {data.isActiveAttack && (
        <span className="asset-topology-node__active-marker" title="Active operation">Active operation</span>
      )}
      <span className="asset-topology-node__marker" aria-hidden />
      <div className="asset-topology-node__content">
        <span className="asset-topology-node__type">
          {data.assetType}
        </span>
        <span className="asset-topology-node__label" title={data.label}>
          {data.label.length > 22 ? `${data.label.slice(0, 20)}…` : data.label}
        </span>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="asset-topology-node__handle"
      />
    </div>
  );
});

const nodeTypes = { asset: AssetNode };

function displayType(node: AssetMapNode): string {
  const legacyType = node.metadata.attributes.legacyType;
  return typeof legacyType === 'string' ? legacyType : node.kind;
}

function topologyTone(assetType: string): TopologyTone {
  switch (assetType) {
    case 'attackvector': return 'purple';
    case 'dnsrecord': return 'cyan';
    case 'endpoint': return 'blue';
    case 'ip': return 'amber';
    case 'port': return 'amber';
    case 'seed': return 'blue';
    case 'subdomain': return 'green';
    case 'target': return 'purple';
    case 'techstack': return 'green';
    case 'url': return 'cyan';
    case 'vulnerability': return 'red';
    default: return 'cyan';
  }
}

function deduplicateDisplayEdges(edges: readonly AssetMapEdge[]): AssetMapEdge[] {
  const edgeIds = new Set<string>();

  return edges.filter((edge) => {
    if (edgeIds.has(edge.id)) return false;
    edgeIds.add(edge.id);
    return true;
  });
}

function isAssetNodeData(data: unknown): data is AssetNodeData {
  return typeof data === 'object' && data !== null && 'tone' in data && typeof data.tone === 'string';
}

function assetFlowNodeColor(node: Node): string {
  return isAssetNodeData(node.data) ? TONE_VARIABLE[node.data.tone] : 'var(--text-muted)';
}

function buildGraph(graphNodes: readonly AssetMapNode[], edges: readonly AssetMapEdge[]): {
  nodes: AssetFlowNode[];
  edges: AssetFlowEdge[];
} {
  // Sort by preferred rank so dagre tends to stack layers predictably
  const sorted = [...graphNodes].sort(
    (a, b) => (TYPE_RANK[displayType(a)] ?? 2) - (TYPE_RANK[displayType(b)] ?? 2),
  );

  const nodes: AssetFlowNode[] = sorted.map((n) => {
    const assetType = displayType(n);
    const tone = topologyTone(assetType);
    return {
      id: n.id,
      type: 'asset',
      position: { x: 0, y: 0 },
      data: {
        label: n.label,
        assetType,
        tone,
        isActiveAttack: n.metadata.isActive,
        assetNode: n,
      },
      width: 168,
      height: 52,
    };
  });

  const flowEdges: AssetFlowEdge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    label: e.label ?? undefined,
    markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
    data: { edgeType: e.kind },
    labelBgPadding: [4, 2],
  }));

  const laidOut = layoutWithDagre(nodes, flowEdges, {
    direction: 'TB',
    nodeWidth: 168,
    nodeHeight: 52,
    nodesep: 28,
    ranksep: 70,
  });

  return { nodes: laidOut, edges: flowEdges };
}

function TopologyFlowInner({
  graph,
  displayEdges,
  onSelectNode,
  selectedNodeId,
}: {
  graph: AssetMapGraph;
  displayEdges: readonly AssetMapEdge[];
  onSelectNode?: (node: AssetMapNode) => void;
  selectedNodeId?: string | null;
}) {
  const { fitView } = useReactFlow();
  const built = useMemo(() => buildGraph(graph.nodes, displayEdges), [graph.nodes, displayEdges]);
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

  const onNodeClick: NodeMouseHandler<AssetFlowNode> = useCallback(
    (_evt, node) => {
      onSelectNode?.(node.data.assetNode);
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
      className="asset-topology-map__flow"
    >
      <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="var(--border-subtle)" />
      <Controls
        showInteractive={false}
        className="asset-topology-map__controls"
      />
      <MiniMap
        className="asset-topology-map__minimap"
        nodeColor={assetFlowNodeColor}
        maskColor="var(--bg-card)"
        pannable
        zoomable
      />
    </ReactFlow>
  );
}

export function AssetTopologyMap({ graph, onSelectNode, selectedNodeId }: AssetTopologyMapProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const onFullscreenToggle = useCallback(() => setIsFullscreen((prev) => !prev), []);

  if (!graph) {
    return <div className="asset-topology-map__empty">Select a target-bound thread to view topology</div>;
  }

  if (graph.nodes.length === 0) {
    return <div className="asset-topology-map__empty">No assets to display</div>;
  }

  const displayEdges = deduplicateDisplayEdges(graph.edges);
  const target = graph.nodes.find((node) => node.id === graph.targetId);
  const activeNodeCount = graph.nodes.filter((node) => node.metadata.isActive).length;

  return (
    <>
      <div
        className="asset-topology-map"
        data-testid="asset-topology-map"
      >
        <div className="asset-topology-map__header">
          <span className="asset-topology-map__title">Topology · {target?.label ?? graph.targetId}</span>
          <span className="asset-topology-map__summary">
            {graph.nodes.length} nodes · {displayEdges.length} edges
            {activeNodeCount > 0
              ? ` · ${activeNodeCount} active`
              : ''}
          </span>
          <button
            type="button"
            className="c2-btn c2-btn--ghost c2-btn--icon"
            onClick={onFullscreenToggle}
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? <Minimize2 aria-hidden="true" size={18} /> : <Maximize2 aria-hidden="true" size={18} />}
          </button>
        </div>
        <div className="w-full h-[360px] min-h-[280px]">
          <ReactFlowProvider>
            <TopologyFlowInner
              graph={graph}
              displayEdges={displayEdges}
              onSelectNode={onSelectNode}
              selectedNodeId={selectedNodeId}
            />
          </ReactFlowProvider>
        </div>
        <div className="asset-topology-map__legend">
          {Object.entries(TYPE_TONE).map(([type, tone]) => (
            <span key={type} className={`asset-topology-map__legend-item asset-topology-map__legend-item--${tone}`}>
              <i className="asset-topology-map__legend-marker" />
              {type}
            </span>
          ))}
        </div>
      </div>

      {/* Fullscreen Dialog */}
      <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
        <DialogContent className="max-w-full w-[calc(100%-2rem)] h-[calc(100vh-120px)] p-4">
          <DialogHeader>
            <DialogTitle>Asset Map (Fullscreen)</DialogTitle>
          </DialogHeader>
          <div className="h-full w-full">
            <ReactFlowProvider>
              <TopologyFlowInner
                graph={graph}
                displayEdges={displayEdges}
                onSelectNode={onSelectNode}
                selectedNodeId={selectedNodeId}
              />
            </ReactFlowProvider>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default AssetTopologyMap;
