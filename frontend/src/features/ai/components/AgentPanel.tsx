import type { ReactNode } from 'react';
import type { AgentInteractionTree, TargetTopology, TopologyNode } from '../services/aiApi';
import AgentInteractionTimeline from '../../../components/AgentInteractionTimeline';
import AssetTopologyMap from '../../../components/AssetTopologyMap';
import AssetDetailPanel from '../../../components/AssetDetailPanel';
import { TreeNodeItem, type TreeNode } from './TreePanel';

interface AgentPanelProps {
  showTree: boolean;
  showTreePanel: boolean;
  onClose: () => void;
  treeConnected: boolean;
  agentPanelTab: 'tree' | 'interaction' | 'topology';
  onTabChange: (tab: 'tree' | 'interaction' | 'topology') => void;
  agentTree: TreeNode[];
  rootNode: TreeNode | null;
  activeNodeThreadId: string | null;
  onSelectTreeNode: (node: TreeNode) => void;
  dispatchTree: AgentInteractionTree | null;
  boundTargetId: number | null;
  onOpenGraph: (graphId: number) => void;
  onOpenLogsPanel: () => void;
  topology: TargetTopology | null;
  selectedTopoNode: TopologyNode | null;
  onSelectTopoNode: (node: TopologyNode | null) => void;
}

const TABS: { key: 'tree' | 'interaction' | 'topology'; label: string }[] = [
  { key: 'tree', label: 'Tree' },
  { key: 'interaction', label: 'Interaction' },
  { key: 'topology', label: 'Topology' },
];

export function AgentPanel({
  showTree,
  showTreePanel: _showTreePanel,
  onClose,
  treeConnected,
  agentPanelTab,
  onTabChange,
  agentTree,
  rootNode,
  activeNodeThreadId,
  onSelectTreeNode,
  dispatchTree,
  boundTargetId,
  onOpenGraph,
  onOpenLogsPanel,
  topology,
  selectedTopoNode,
  onSelectTopoNode,
}: AgentPanelProps): ReactNode {
  if (!showTree) return null;

  return (
    <aside className="agent-tree-panel agent-tree-panel--wide">
      <div className="tree-panel-header">
        <h4>AGENTS</h4>
        <div className="tree-panel-actions">
          <span
            className={`tree-live-dot ${treeConnected ? 'connected' : 'disconnected'}`}
            title={treeConnected ? 'Live — auto-updating' : 'Disconnected'}
          />
          <button className="tree-action-btn" onClick={onClose} title="Close">✕</button>
        </div>
      </div>

      <div className="agent-panel-tabs">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            className={`agent-panel-tab ${agentPanelTab === key ? 'active' : ''}`}
            onClick={() => onTabChange(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="tree-body">
        {agentPanelTab === 'tree' && (
          <>
            {agentTree.length === 0 && (
              <div className="tree-empty">No sub-agents yet</div>
            )}
            {rootNode && (
              <TreeNodeItem
                node={rootNode}
                depth={0}
                allNodes={agentTree}
                activeNodeThreadId={activeNodeThreadId}
                onSelect={onSelectTreeNode}
              />
            )}
          </>
        )}

        {agentPanelTab === 'interaction' && (
          <AgentInteractionTimeline
            tree={dispatchTree}
            selectedThreadId={activeNodeThreadId ? Number(activeNodeThreadId) : null}
            onSelectNode={(n) => {
              if (!n.thread_id) return;
              onSelectTreeNode({
                thread_id: n.thread_id,
                thread_name: n.agent_id ?? `Thread ${n.thread_id}`,
                assistant_id: n.agent_id ?? 'automation_agent',
                is_hidden: true,
                bound_target_id: boundTargetId,
                parent_thread_id: null,
                overview_id: null,
                overview_status: null,
                overview_risk_score: null,
                target_name: null,
                created_at: n.dispatched_at ?? '',
              });
              if (n.graph_id) {
                onOpenGraph(n.graph_id);
                onOpenLogsPanel();
              }
            }}
          />
        )}

        {agentPanelTab === 'topology' && (
          <div className="topology-panel-stack">
            <AssetTopologyMap
              topology={topology}
              selectedNodeId={selectedTopoNode?.id ?? null}
              onSelectNode={onSelectTopoNode}
            />
            {selectedTopoNode && (
              <AssetDetailPanel
                node={selectedTopoNode}
                onClose={() => onSelectTopoNode(null)}
                onOpenGraph={(gid) => {
                  onOpenGraph(gid);
                  onOpenLogsPanel();
                }}
              />
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
