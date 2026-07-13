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

import type { AgentInteractionNode, AgentInteractionTree } from '../services/executionApi';
import { layoutWithDagre } from '../utils/graphLayout';
import './AgentInteractionTimeline.css';

interface AgentInteractionTimelineProps {
  tree: AgentInteractionTree | null;
  onSelectNode?: (node: AgentInteractionNode) => void;
  selectedThreadId?: number | null;
}

const STATUS_COLOR: Record<string, string> = {
  ROOT: '#94a3b8',
  RUNNING: '#38bdf8',
  COMPLETED: '#4ade80',
  SUCCEEDED: '#4ade80',
  FAILED: '#f87171',
  WAITING: '#fbbf24',
};

type AgentNodeData = {
  label: string;
  meta: string;
  status: string;
  color: string;
  agentNode: AgentInteractionNode;
};

type AgentFlowNode = Node<AgentNodeData, 'agent'>;
type AgentFlowEdge = Edge;

const NODE_W = 172;
const NODE_H = 56;

const AgentNode = memo(function AgentNode({ data, selected }: NodeProps<AgentFlowNode>) {
  return (
    <div
      className={['ait-rf-node', selected ? 'ait-rf-node--selected' : ''].filter(Boolean).join(' ')}
      style={{ borderColor: data.color, ['--ait-color' as string]: data.color }}
    >
      <Handle type="target" position={Position.Top} className="ait-rf-handle" />
      <div className="ait-rf-title-row">
        <span className="ait-rf-title" title={data.label}>
          {data.label.length > 22 ? `${data.label.slice(0, 20)}…` : data.label}
        </span>
        {data.status !== 'ROOT' && <span className="ait-rf-status-dot" style={{ background: data.color }} />}
      </div>
      <span className="ait-rf-meta">{data.meta}</span>
      <Handle type="source" position={Position.Bottom} className="ait-rf-handle" />
    </div>
  );
});

const nodeTypes = { agent: AgentNode };

function flattenTree(
  nodes: AgentInteractionNode[],
  parentId: string | null,
  accNodes: AgentFlowNode[],
  accEdges: AgentFlowEdge[],
) {
  for (const n of nodes) {
    const id = n.dispatch_id != null ? `d-${n.dispatch_id}` : `t-${n.thread_id}-${n.depth}`;
    const color = STATUS_COLOR[n.status] || '#94a3b8';
    const metaParts = [
      `T#${n.thread_id}`,
      n.round > 0 ? `R${n.round}` : null,
      n.graph_id ? `G#${n.graph_id}` : null,
      n.status !== 'ROOT' ? n.status : null,
    ].filter(Boolean);

    accNodes.push({
      id,
      type: 'agent',
      position: { x: 0, y: 0 },
      data: {
        label: n.agent_id || 'agent',
        meta: metaParts.join(' · '),
        status: n.status,
        color,
        agentNode: n,
      },
      width: NODE_W,
      height: NODE_H,
    });

    if (parentId) {
      accEdges.push({
        id: `e-${parentId}-${id}`,
        source: parentId,
        target: id,
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: '#475569' },
        style: { stroke: '#475569', strokeWidth: 1.5 },
      });
    }

    if (n.children?.length) {
      flattenTree(n.children, id, accNodes, accEdges);
    }
  }
}

function buildGraph(tree: AgentInteractionTree): {
  nodes: AgentFlowNode[];
  edges: AgentFlowEdge[];
} {
  const rootId = `root-${tree.root_thread_id}`;
  const rootAgent: AgentInteractionNode = {
    thread_id: tree.root_thread_id,
    agent_id: tree.root_agent_id || 'hacker_assistant_agent',
    status: 'ROOT',
    depth: 0,
    round: 0,
    objective: 'Root conversation',
    children: tree.nodes || [],
  };

  const nodes: AgentFlowNode[] = [];
  const edges: AgentFlowEdge[] = [];

  nodes.push({
    id: rootId,
    type: 'agent',
    position: { x: 0, y: 0 },
    data: {
      label: rootAgent.agent_id,
      meta: `T#${rootAgent.thread_id} · root`,
      status: 'ROOT',
      color: STATUS_COLOR.ROOT,
      agentNode: rootAgent,
    },
    width: NODE_W,
    height: NODE_H,
  });

  flattenTree(rootAgent.children, rootId, nodes, edges);

  const laidOut = layoutWithDagre(nodes, edges, {
    direction: 'TB',
    nodeWidth: NODE_W,
    nodeHeight: NODE_H,
    nodesep: 32,
    ranksep: 64,
  });

  return { nodes: laidOut, edges };
}

function InteractionFlowInner({
  tree,
  onSelectNode,
  selectedThreadId,
}: {
  tree: AgentInteractionTree;
  onSelectNode?: (node: AgentInteractionNode) => void;
  selectedThreadId?: number | null;
}) {
  const { fitView } = useReactFlow();
  const built = useMemo(() => buildGraph(tree), [tree]);
  const [nodes, setNodes, onNodesChange] = useNodesState(built.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(built.edges);

  useEffect(() => {
    setNodes(built.nodes);
    setEdges(built.edges);
    const t = requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 200 });
    });
    return () => cancelAnimationFrame(t);
  }, [built, setNodes, setEdges, fitView]);

  useEffect(() => {
    setNodes((prev) =>
      prev.map((n) => {
        const data = n.data as AgentNodeData;
        const selected =
          selectedThreadId != null && data?.agentNode?.thread_id === selectedThreadId;
        return { ...n, selected };
      }),
    );
  }, [selectedThreadId, setNodes]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_evt, node) => {
      const data = node.data as AgentNodeData;
      if (data?.agentNode && data.status !== 'ROOT') {
        onSelectNode?.(data.agentNode);
      }
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
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.25}
      maxZoom={1.6}
      proOptions={{ hideAttribution: true }}
      nodesConnectable={false}
      edgesReconnectable={false}
      elementsSelectable
      panOnScroll
      colorMode="dark"
      className="ait-rf-canvas"
    >
      <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#1e293b" />
      <Controls showInteractive={false} className="ait-rf-controls" />
      <MiniMap
        className="ait-rf-minimap"
        nodeColor={(n) => (n.data as AgentNodeData)?.color || '#475569'}
        maskColor="rgba(15, 23, 42, 0.75)"
        pannable
        zoomable
      />
    </ReactFlow>
  );
}

export function AgentInteractionTimeline({
  tree,
  onSelectNode,
  selectedThreadId,
}: AgentInteractionTimelineProps) {
  if (!tree) {
    return <div className="ait-empty">No dispatch tree</div>;
  }

  if ((tree.nodes || []).length === 0) {
    return (
      <div className="ait-empty">
        No sub-agent dispatches yet for Thread #{tree.root_thread_id}
      </div>
    );
  }

  return (
    <div className="agent-interaction-timeline" data-testid="agent-interaction-timeline">
      <div className="ait-rf-viewport">
        <ReactFlowProvider>
          <InteractionFlowInner
            tree={tree}
            onSelectNode={onSelectNode}
            selectedThreadId={selectedThreadId}
          />
        </ReactFlowProvider>
      </div>
    </div>
  );
}

export default AgentInteractionTimeline;
