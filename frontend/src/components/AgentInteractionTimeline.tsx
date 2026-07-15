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

import type { AgentInteractionNode, AgentInteractionTree } from '../services/executionApi';
import { layoutWithDagre } from '../utils/graphLayout';

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

const NODE_W = 204;
const NODE_H = 68;

const AgentNode = memo(function AgentNode({ data, selected }: NodeProps<AgentFlowNode>) {
  return (
    <div
      className={cn(
        'min-w-[184px] max-w-[212px] py-2.5 px-3 pb-3 rounded-[10px] border-[1.5px] border-[#475569] bg-[#0f172a] shadow-[0_2px_10px_rgba(0,0,0,0.35)] font-body cursor-pointer hover:bg-[#1e293b]',
        selected && 'bg-[#1e293b] shadow-[0_0_0_2px_rgba(34,197,94,0.4),0_0_12px_rgba(34,197,94,0.2)]',
      )}
      style={{ borderColor: data.color, ['--ait-color' as string]: data.color }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-1.5 !h-1.5 !bg-[#334155] !border !border-[#64748b] opacity-75"
      />
      <div className="flex items-center justify-between gap-1.5">
        <span
          className="text-[#e2e8f0] text-[13px] font-['Fira_Code',ui-monospace,monospace] font-semibold whitespace-nowrap overflow-hidden text-ellipsis"
          title={data.label}
        >
          {data.label.length > 22 ? `${data.label.slice(0, 20)}…` : data.label}
        </span>
        {data.status !== 'ROOT' && <span className="w-2 h-2 rounded-full shrink-0" style={{ background: data.color }} />}
      </div>
      <span className="block mt-1 text-[#94a3b8] text-[12px] whitespace-nowrap overflow-hidden text-ellipsis">{data.meta}</span>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-1.5 !h-1.5 !bg-[#334155] !border !border-[#64748b] opacity-75"
      />
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
      className="bg-transparent"
    >
      <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#1e293b" />
      <Controls
        showInteractive={false}
        className="!bg-[#0f172a] !border !border-[#1e293b] !rounded-lg !shadow-none [&_button]:!bg-[#0f172a] [&_button]:!border-b-[#1e293b] [&_button]:!fill-[#94a3b8] [&_button:hover]:!bg-[#1e293b]"
      />
      <MiniMap
        className="!bg-[#0f172a] !border !border-[#1e293b] !rounded-lg"
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
    return <div className="p-6 text-center text-[#64748b] text-[0.78rem]">No dispatch tree</div>;
  }

  if ((tree.nodes || []).length === 0) {
    return (
      <div className="p-6 text-center text-[#64748b] text-[0.78rem]">
        No sub-agent dispatches yet for Thread #{tree.root_thread_id}
      </div>
    );
  }

  return (
    <div
      className="w-full bg-[radial-gradient(ellipse_at_top,rgba(30,41,59,0.6),transparent_70%),#0b1220] rounded-[10px] border border-[#1e293b] overflow-hidden"
      data-testid="agent-interaction-timeline"
    >
      <div className="w-full h-[340px] min-h-[240px]">
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
