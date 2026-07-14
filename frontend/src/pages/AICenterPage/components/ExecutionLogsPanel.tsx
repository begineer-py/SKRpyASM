import ExecutionTimelineViewer from '../../../components/ExecutionTimelineViewer';
import type { ExecutionGraph } from '../../../services/executionApi';

interface ExecutionLogsPanelProps {
  selectedGraphId: number | null;
  activeThreadGraphs: ExecutionGraph[];
  graphStatusFilter: string;
  graphHasMore: boolean;
  onSelectGraph: (id: number) => void;
  onStatusFilterChange: (filter: string) => void;
  onArchiveGraph: (id: number) => void;
  onDeleteGraph: (id: number) => void;
  onLoadMore: () => void;
  onClose: () => void;
}

const ExecutionLogsPanel: React.FC<ExecutionLogsPanelProps> = ({
  selectedGraphId,
  activeThreadGraphs,
  graphStatusFilter,
  graphHasMore,
  onSelectGraph,
  onStatusFilterChange,
  onArchiveGraph,
  onDeleteGraph,
  onLoadMore,
  onClose,
}) => {
  return (
    <div className="logs-panel">
      <div className="logs-panel-header">
        <div className="logs-panel-title">
          <span>EXECUTION GRAPH</span>
          {selectedGraphId && <span className="logs-graph-status">Graph #{selectedGraphId}</span>}
        </div>

        <div className="logs-panel-controls">
          <select
            className="graph-picker"
            value={graphStatusFilter}
            onChange={(e) => {
              onStatusFilterChange(e.target.value);
            }}
            title="Filter by status"
          >
            <option value="">All</option>
            <option value="RUNNING">Running</option>
            <option value="WAITING">Waiting</option>
            <option value="SUCCEEDED">Succeeded</option>
            <option value="FAILED">Failed</option>
          </select>
          {activeThreadGraphs.length > 0 && (
            <select
              className="graph-picker"
              value={selectedGraphId ?? ''}
              onChange={e => onSelectGraph(Number(e.target.value))}
            >
              {activeThreadGraphs.map(graph => (
                <option key={graph.id} value={graph.id}>
                  #{graph.id} [{graph.status}] {graph.title || graph.assistant_id}
                </option>
              ))}
            </select>
          )}
          {selectedGraphId && (
            <>
              <button
                className="logs-close-btn"
                onClick={() => onArchiveGraph(selectedGraphId)}
                title="Archive graph"
              >Archive</button>
              <button
                className="logs-close-btn"
                onClick={() => onDeleteGraph(selectedGraphId)}
                title="Delete graph"
              >Delete</button>
            </>
          )}
          <button
            className="logs-close-btn"
            onClick={onClose}
            title="Close logs panel"
          >✕</button>
        </div>
      </div>

      <div className="logs-panel-body">
        {selectedGraphId ? (
          <ExecutionTimelineViewer graphId={selectedGraphId} compact autoScroll />
        ) : (
          <div className="logs-empty">No execution graph selected</div>
        )}
        {graphHasMore && (
          <div className="p-2 text-center">
            <button
              className="c2-btn c2-btn--ghost c2-btn--sm"
              onClick={onLoadMore}
            >
              Load More
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionLogsPanel;
