import { useCallback, type KeyboardEvent, type ReactNode, type RefObject } from 'react';
import type { AgentInteractionTree, TargetTopology, TopologyNode } from '../services/aiApi';
import AgentInteractionTimeline from '../../../components/AgentInteractionTimeline';
import AssetTopologyMap from '../../../components/AssetTopologyMap';
import AssetDetailPanel from '../../../components/AssetDetailPanel';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerDismiss,
  DrawerHeader,
  DrawerTitle,
} from '../../../components/ui/drawer';
import { TreeNodeItem, type TreeNode } from './TreePanel';

interface AgentPanelProps {
  showTree: boolean;
  onClose: () => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
  agentPanelTab: 'tree' | 'interaction' | 'topology';
  onTabChange: (tab: 'tree' | 'interaction' | 'topology') => void;
  agentTree: TreeNode[];
  rootNode: TreeNode | null;
  activeNodeThreadId: string | null;
  onSelectTreeNode: (node: TreeNode) => void;
  dispatchTree: AgentInteractionTree | null;
  boundTargetId: number | null;
  onOpenGraph: (graphId: number) => void;
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
  onClose,
  triggerRef,
  agentPanelTab,
  onTabChange,
  agentTree,
  rootNode,
  activeNodeThreadId,
  onSelectTreeNode,
  dispatchTree,
  boundTargetId,
  onOpenGraph,
  topology,
  selectedTopoNode,
  onSelectTopoNode,
}: AgentPanelProps): ReactNode {
  const onTabKeyDown = useCallback((event: KeyboardEvent<HTMLButtonElement>, currentTab: number) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const nextTab = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? TABS.length - 1
        : (currentTab + (event.key === 'ArrowRight' ? 1 : -1) + TABS.length) % TABS.length;
    onTabChange(TABS[nextTab].key);
    document.getElementById(`ai-agent-tab-${TABS[nextTab].key}`)?.focus();
  }, [onTabChange]);

  return (
    <Drawer open={showTree} onOpenChange={(open) => {
      if (!open) {
        onClose();
        window.requestAnimationFrame(() => triggerRef.current?.focus());
      }
    }}>
      <DrawerContent
        id="ai-agent-context-drawer"
        aria-describedby="ai-agent-context-description"
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          triggerRef.current?.focus();
        }}
      >
        <DrawerHeader>
          <div>
            <DrawerTitle>Agent context</DrawerTitle>
            <DrawerDescription id="ai-agent-context-description">
              Inspect delegated agents, their relationships, and target topology when needed.
            </DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>

      <div className="agent-panel-tabs mt-6" role="tablist" aria-label="Agent context views">
        {TABS.map(({ key, label }, index) => (
          <button
            key={key}
            id={`ai-agent-tab-${key}`}
            type="button"
            role="tab"
            className={`agent-panel-tab ${agentPanelTab === key ? 'active' : ''}`}
            onClick={() => onTabChange(key)}
            onKeyDown={(event) => onTabKeyDown(event, index)}
            aria-controls={`ai-agent-panel-${key}`}
            aria-selected={agentPanelTab === key}
            tabIndex={agentPanelTab === key ? 0 : -1}
          >
            {label}
          </button>
        ))}
      </div>

      <div
        id={`ai-agent-panel-${agentPanelTab}`}
        className="tree-body mt-4"
        role="tabpanel"
        aria-labelledby={`ai-agent-tab-${agentPanelTab}`}
      >
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
                onOpenGraph={onOpenGraph}
              />
            )}
          </div>
        )}
      </div>
      </DrawerContent>
    </Drawer>
  );
}
