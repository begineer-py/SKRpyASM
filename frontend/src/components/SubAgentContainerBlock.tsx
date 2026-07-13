import { useState } from 'react';
import ExecutionTimelineViewer from './ExecutionTimelineViewer';
import BlobPageViewer from './BlobPageViewer';
import type { SubAgentDispatchItem } from '../services/executionApi';
import './SubAgentContainerBlock.css';

export interface DispatchedGraphView {
  dispatch_id: number;
  graph_id: number | null;
  status: string;
  title: string;
  dispatch_instruction: string;
  sub_agent_type: string;
  callee_thread_id: number | null;
  result_summary?: string;
  content_blobs: Array<{
    blob_id: number;
    ai_summary: string;
    content_size: number;
    page_count: number | null;
    created_at?: string | null;
  }>;
}

interface SubAgentContainerBlockProps {
  graph: DispatchedGraphView;
  onViewGraph?: (graphId: number) => void;
  onViewThread?: (threadId: number) => void;
}

export function dispatchToView(d: SubAgentDispatchItem): DispatchedGraphView {
  return {
    dispatch_id: d.dispatch_id,
    graph_id: d.graph?.graph_id ?? null,
    status: d.graph?.status || d.status,
    title: d.graph?.title || d.sub_agent_type,
    dispatch_instruction: d.objective || d.result_summary || '',
    sub_agent_type: d.sub_agent_type,
    callee_thread_id: d.callee_thread_id,
    result_summary: d.result_summary,
    content_blobs: (d.content_blobs || []).map((b) => ({
      blob_id: b.blob_id,
      ai_summary: b.ai_summary || '',
      content_size: b.content_size || 0,
      page_count: b.page_count,
      created_at: b.created_at,
    })),
  };
}

const STATUS_CLASS: Record<string, string> = {
  RUNNING: 'running',
  WAITING: 'waiting',
  COMPLETED: 'completed',
  SUCCEEDED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

export function SubAgentContainerBlock({ graph, onViewGraph, onViewThread }: SubAgentContainerBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const [activeBlobPage, setActiveBlobPage] = useState<{ blobId: number; page: number } | null>(null);
  const statusKey = STATUS_CLASS[graph.status] || 'neutral';
  const instruction = graph.dispatch_instruction || '(no objective)';

  return (
    <div className="subagent-container-block" data-testid={`subagent-block-${graph.dispatch_id}`}>
      <div className="scb-header" onClick={() => setExpanded((v) => !v)} role="button" tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setExpanded((v) => !v); }}
      >
        <span className="scb-badge">🤖 AI Sub-agent</span>
        <span className="scb-agent-type">{graph.sub_agent_type}</span>
        <span className={`scb-status scb-status--${statusKey}`}>{graph.status}</span>
        {graph.content_blobs.length > 0 && (
          <span className="scb-blob-count">
            {graph.content_blobs.length} blob{graph.content_blobs.length > 1 ? 's' : ''}
          </span>
        )}
        <span className="scb-toggle">{expanded ? '▲' : '▼'}</span>
      </div>

      <div className="scb-instruction">
        <code>
          {instruction.slice(0, 150)}
          {instruction.length > 150 ? '…' : ''}
        </code>
      </div>

      {graph.result_summary && !expanded && (
        <div className="scb-result-preview">{graph.result_summary.slice(0, 200)}</div>
      )}

      {expanded && (
        <div className="scb-body">
          {graph.content_blobs.length === 0 && (
            <div className="scb-empty">No ContentBlob artifacts yet</div>
          )}
          {graph.content_blobs.map((blob) => (
            <div key={blob.blob_id} className="scb-blob-item">
              <div className="scb-blob-header">
                <span>Blob #{blob.blob_id}</span>
                <span className="scb-blob-size">{(blob.content_size / 1000).toFixed(1)}k chars</span>
                {blob.page_count != null && blob.page_count > 0 && (
                  <span className="scb-blob-pages">{blob.page_count} pages</span>
                )}
              </div>
              {blob.ai_summary && <div className="scb-blob-summary">{blob.ai_summary}</div>}
              {blob.page_count != null && blob.page_count > 1 && (
                <div className="scb-blob-pages-nav">
                  {Array.from({ length: blob.page_count }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={`scb-page-btn ${activeBlobPage?.blobId === blob.blob_id && activeBlobPage.page === p ? 'active' : ''}`}
                      onClick={() => setActiveBlobPage({ blobId: blob.blob_id, page: p })}
                    >
                      P{p}
                    </button>
                  ))}
                </div>
              )}
              {activeBlobPage?.blobId === blob.blob_id && (
                <BlobPageViewer blobId={activeBlobPage.blobId} page={activeBlobPage.page} />
              )}
            </div>
          ))}

          {graph.graph_id != null && (
            <div className="scb-timeline">
              <ExecutionTimelineViewer graphId={graph.graph_id} compact autoScroll={false} />
            </div>
          )}
        </div>
      )}

      <div className="scb-actions">
        {graph.callee_thread_id != null && onViewThread && (
          <button type="button" className="scb-btn" onClick={() => onViewThread(graph.callee_thread_id!)}>
            Thread
          </button>
        )}
        {graph.graph_id != null && onViewGraph && (
          <button type="button" className="scb-btn" onClick={() => onViewGraph(graph.graph_id!)}>
            Full Graph
          </button>
        )}
      </div>
    </div>
  );
}

export default SubAgentContainerBlock;
