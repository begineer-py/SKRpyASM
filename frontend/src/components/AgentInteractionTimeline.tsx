import { useMemo } from 'react';
import type { AgentInteractionNode, AgentInteractionTree } from '../services/executionApi';
import './AgentInteractionTimeline.css';

interface AgentInteractionTimelineProps {
  tree: AgentInteractionTree | null;
  onSelectNode?: (node: AgentInteractionNode) => void;
  selectedThreadId?: number | null;
}

interface LaidOutNode extends AgentInteractionNode {
  x: number;
  y: number;
  parentX?: number;
  parentY?: number;
}

const NODE_W = 160;
const NODE_H = 52;
const H_GAP = 40;
const V_GAP = 70;

function layoutTree(
  nodes: AgentInteractionNode[],
  depth: number,
  startX: number,
  yBase: number,
): { laid: LaidOutNode[]; width: number } {
  if (nodes.length === 0) return { laid: [], width: 0 };

  const laid: LaidOutNode[] = [];
  let cursorX = startX;

  for (const node of nodes) {
    const { laid: childLaid, width: childW } = layoutTree(
      node.children || [],
      depth + 1,
      cursorX,
      yBase + V_GAP,
    );
    const selfW = Math.max(NODE_W + H_GAP, childW);
    const x = cursorX + selfW / 2 - NODE_W / 2;
    const y = yBase;

    laid.push({ ...node, x, y });
    for (const c of childLaid) {
      laid.push({
        ...c,
        parentX: x + NODE_W / 2,
        parentY: y + NODE_H,
      });
    }
    cursorX += selfW;
  }

  return { laid, width: cursorX - startX };
}

const STATUS_COLOR: Record<string, string> = {
  RUNNING: '#38bdf8',
  COMPLETED: '#4ade80',
  SUCCEEDED: '#4ade80',
  FAILED: '#f87171',
  WAITING: '#fbbf24',
};

export function AgentInteractionTimeline({
  tree,
  onSelectNode,
  selectedThreadId,
}: AgentInteractionTimelineProps) {
  const { laid, width, height } = useMemo(() => {
    if (!tree) return { laid: [] as LaidOutNode[], width: 400, height: 120 };

    const rootNode: AgentInteractionNode = {
      thread_id: tree.root_thread_id,
      agent_id: tree.root_agent_id || 'hacker_assistant_agent',
      status: 'ROOT',
      depth: 0,
      round: 0,
      objective: 'Root conversation',
      children: tree.nodes || [],
    };

    const { laid: childrenLaid, width: childW } = layoutTree(
      rootNode.children,
      1,
      20,
      V_GAP + 20,
    );
    const totalW = Math.max(400, childW + 40, NODE_W + 40);
    const rootX = totalW / 2 - NODE_W / 2;
    const root: LaidOutNode = {
      ...rootNode,
      x: rootX,
      y: 16,
    };
    const withParent = childrenLaid.map((c) =>
      c.depth === 1
        ? { ...c, parentX: rootX + NODE_W / 2, parentY: 16 + NODE_H }
        : c,
    );
    const all = [root, ...withParent];
    const maxY = all.reduce((m, n) => Math.max(m, n.y), 0) + NODE_H + 30;
    return { laid: all, width: totalW, height: maxY };
  }, [tree]);

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
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={Math.min(height, 360)}>
        {/* edges */}
        {laid.map((n) => {
          if (n.parentX == null || n.parentY == null) return null;
          const x2 = n.x + NODE_W / 2;
          const y2 = n.y;
          const midY = (n.parentY + y2) / 2;
          return (
            <path
              key={`e-${n.dispatch_id ?? n.thread_id}-${n.depth}`}
              d={`M ${n.parentX} ${n.parentY} C ${n.parentX} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
              className="ait-edge"
              fill="none"
            />
          );
        })}

        {/* nodes */}
        {laid.map((n) => {
          const selected = selectedThreadId === n.thread_id;
          const color = STATUS_COLOR[n.status] || '#94a3b8';
          return (
            <g
              key={`n-${n.dispatch_id ?? 'root'}-${n.thread_id}`}
              transform={`translate(${n.x}, ${n.y})`}
              className={`ait-node ${selected ? 'ait-node--selected' : ''}`}
              onClick={() => onSelectNode?.(n)}
              style={{ cursor: onSelectNode ? 'pointer' : 'default' }}
            >
              <rect
                width={NODE_W}
                height={NODE_H}
                rx={8}
                className="ait-node-rect"
                stroke={color}
              />
              <text x={10} y={18} className="ait-node-title">
                {(n.agent_id || 'agent').slice(0, 22)}
              </text>
              <text x={10} y={34} className="ait-node-meta">
                T#{n.thread_id}
                {n.round > 0 ? ` · R${n.round}` : ''}
                {n.graph_id ? ` · G#${n.graph_id}` : ''}
              </text>
              {n.status !== 'ROOT' && (
                <circle cx={NODE_W - 12} cy={12} r={5} fill={color} />
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default AgentInteractionTimeline;
