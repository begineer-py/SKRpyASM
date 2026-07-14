/* eslint-disable react-refresh/only-export-components -- tree rendering and its pure data adapter share one feature contract. */
import type { ReactNode } from 'react';

// ── Status badge helpers ──────────────────────────────────────────────────

export const STATUS_CLASS: Record<string, string> = {
  EXECUTING:         'tree-badge--executing',
  PLANNING:          'tree-badge--planning',
  COMPLETED:         'tree-badge--completed',
  FAILED:            'tree-badge--failed',
  NEEDS_GUIDANCE:    'tree-badge--needs-guidance',
  WAITING_FOR_ASYNC: 'tree-badge--waiting',
};

const STATUS_ICON: Record<string, string> = {
  EXECUTING:         '⟳',
  PLANNING:          '◯',
  COMPLETED:         '✓',
  FAILED:            '✗',
  NEEDS_GUIDANCE:    '?',
  WAITING_FOR_ASYNC: '⏳',
};

const riskClass = (score: number) =>
  score > 66 ? 'high' : score > 33 ? 'medium' : 'low';

// ── Types ─────────────────────────────────────────────────────────────────

export interface TreeNode {
  thread_id: number;
  thread_name: string;
  assistant_id: string;
  is_hidden: boolean;
  bound_target_id: number | null;
  parent_thread_id: number | null;
  overview_id: number | null;
  overview_status: string | null;
  overview_risk_score: number | null;
  target_name: string | null;
  created_at: string;
}

// ── Tree node component ───────────────────────────────────────────────────

export function TreeNodeItem({
  node,
  depth,
  allNodes,
  activeNodeThreadId,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  allNodes: TreeNode[];
  activeNodeThreadId: string | null;
  onSelect: (node: TreeNode) => void;
}): ReactNode {
  const isActive = activeNodeThreadId === String(node.thread_id);
  const icon = node.assistant_id === 'hacker_assistant_agent' ? 'HA' : 'AI';
  const children =
    node.thread_id != null
      ? allNodes.filter(n => n.parent_thread_id === node.thread_id)
      : [];

  return (
    <div className="tree-node-group">
      <div
        className={`tree-node ${isActive ? 'tree-node--active' : ''}`}
        style={{ paddingLeft: `${8 + depth * 20}px` }}
        onClick={() => onSelect(node)}
        title={node.thread_name}
        data-testid={`tree-node-${node.thread_id}`}
        data-status={node.overview_status || 'unknown'}
        data-depth={depth}
      >
        {depth > 0 && <span className="tree-connector" />}
        <div className="tree-node-label">
          <span className="tree-node-icon">{icon}</span>
          <span className="tree-node-name">
            {node.target_name && depth > 0 ? node.target_name : node.thread_name}
          </span>
        </div>
        {node.overview_status && (
          <span
            className={`tree-node-status-icon tree-node-status-icon--${(STATUS_CLASS[node.overview_status] || 'tree-badge--default').replace('tree-badge--', '')}`}
          >
            {STATUS_ICON[node.overview_status] || '•'}
          </span>
        )}
        <div className="tree-node-meta">
          {isActive && !node.overview_status && (
            <span
              className="tree-node-skeleton"
              data-testid={`skeleton-${node.thread_id}`}
            />
          )}
          {node.overview_status && (
            <span className={`tree-badge ${STATUS_CLASS[node.overview_status] || 'tree-badge--default'}`}>
              {node.overview_status.replace(/_/g, ' ')}
            </span>
          )}
          {node.overview_risk_score !== null && (
            <span className={`tree-badge tree-badge--risk ${riskClass(node.overview_risk_score)}`}>
              Risk {node.overview_risk_score}
            </span>
          )}
        </div>
      </div>
      {children.map(child => (
        <TreeNodeItem
          key={child.thread_id}
          node={child}
          depth={depth + 1}
          allNodes={allNodes}
          activeNodeThreadId={activeNodeThreadId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ── Helper: build flat TreeNode[] from GQL subscription data ─────────────

function _ingestThreadFromOv(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  t: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ov: any,
  parentThreadId: number,
  nodes: TreeNode[],
  seen: Set<number>,
): void {
  const tid = Number(t.id);
  if (seen.has(tid)) return;
  seen.add(tid);
  nodes.push({
    thread_id: tid,
    thread_name: t.name,
    assistant_id: t.assistant_id,
    is_hidden: t.is_hidden,
    bound_target_id: t.bound_target_id,
    parent_thread_id: parentThreadId,
    overview_id: Number(ov.id),
    overview_status: ov.status,
    overview_risk_score: ov.risk_score,
    target_name: ov.core_target?.name ?? null,
    created_at: t.created_at,
  });
  for (const childOv of Array.isArray(t.core_overviews) ? t.core_overviews : []) {
    const childT = childOv.aiAssistantThreadByThreadId;
    if (childT) _ingestThreadFromOv(childT, childOv, tid, nodes, seen);
  }
}

export function buildTreeNodes(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rawData: any,
  rootThreadId: string,
): TreeNode[] {
  if (!rawData?.ai_assistant_thread_by_pk) return [];

  const root = rawData.ai_assistant_thread_by_pk;
  const nodes: TreeNode[] = [];
  const seen = new Set<number>();

  nodes.push({
    thread_id: Number(root.id),
    thread_name: root.name,
    assistant_id: root.assistant_id,
    is_hidden: root.is_hidden,
    bound_target_id: root.bound_target_id,
    parent_thread_id: null,
    overview_id: null,
    overview_status: null,
    overview_risk_score: null,
    target_name: null,
    created_at: root.created_at,
  });
  seen.add(Number(root.id));

  for (const ov of Array.isArray(root.core_overviews) ? root.core_overviews : []) {
    const t = ov.aiAssistantThreadByThreadId;
    if (t) _ingestThreadFromOv(t, ov, Number(rootThreadId), nodes, seen);
  }

  return nodes;
}
