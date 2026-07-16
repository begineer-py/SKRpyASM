/* eslint-disable react-refresh/only-export-components -- view adapter and types are intentionally co-located with this UI contract. */
import { useState } from 'react';
import { cn } from '@/lib/utils';
import BlobPageViewer from './BlobPageViewer';
import type { SubAgentDispatchItem } from '../services/executionApi';

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
    callee_thread_id: d.callee_thread_id ?? null,
    result_summary: d.result_summary,
    content_blobs: (d.content_blobs || []).map((b) => ({
      blob_id: b.blob_id,
      ai_summary: b.ai_summary || '',
      content_size: b.content_size || 0,
      page_count: b.page_count ?? null,
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

const STATUS_STYLES: Record<string, string> = {
  running: 'bg-[rgba(56,189,248,0.15)] text-[#38bdf8]',
  waiting: 'bg-[rgba(251,191,36,0.15)] text-[#fbbf24]',
  completed: 'bg-[rgba(34,197,94,0.15)] text-[#4ade80]',
  failed: 'bg-[rgba(239,68,68,0.15)] text-[#f87171]',
  cancelled: 'bg-[rgba(148,163,184,0.15)] text-[#94a3b8]',
  neutral: 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]',
};

export function SubAgentContainerBlock({ graph, onViewGraph, onViewThread }: SubAgentContainerBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const [activeBlobPage, setActiveBlobPage] = useState<{ blobId: number; page: number } | null>(null);
  const statusKey = STATUS_CLASS[graph.status] || 'neutral';
  const instruction = graph.dispatch_instruction || '(no objective)';
  const detailsId = `subagent-details-${graph.dispatch_id}`;

  return (
    <div className="mx-3 my-2.5 border border-[#334155] rounded-xl bg-gradient-to-br from-[rgba(30,41,59,0.9)] to-[rgba(15,23,42,0.95)] overflow-hidden shadow-[0_4px_16px_rgba(0,0,0,0.25)]" data-testid={`subagent-block-${graph.dispatch_id}`}>
      <button
        type="button"
        className="flex w-full items-center gap-2 border-0 bg-transparent px-3 py-2.5 text-left cursor-pointer select-none hover:bg-[rgba(51,65,85,0.35)]"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls={detailsId}
      >
        <span className="text-[0.72rem] font-semibold text-[#a78bfa]">🤖 AI Sub-agent</span>
        <span className="font-['Fira_Code',monospace] text-[0.72rem] text-[#e2e8f0] bg-[#1e293b] px-2 py-0.5 rounded-md">{graph.sub_agent_type}</span>
        <span className={cn(
          'text-[0.68rem] font-semibold px-2 py-0.5 rounded-full uppercase tracking-[0.04em]',
          STATUS_STYLES[statusKey] || STATUS_STYLES.neutral,
        )}>
          {graph.status}
        </span>
        {graph.content_blobs.length > 0 && (
          <span className="text-[0.68rem] text-[#64748b]">
            {graph.content_blobs.length} blob{graph.content_blobs.length > 1 ? 's' : ''}
          </span>
        )}
        <span className="ml-auto text-[#64748b] text-[0.7rem]">{expanded ? '▲' : '▼'}</span>
      </button>

      <div className="px-3 pb-2 [&_code]:block [&_code]:font-['Fira_Code',monospace] [&_code]:text-[0.72rem] [&_code]:text-[#94a3b8] [&_code]:bg-[#0f172a] [&_code]:border [&_code]:border-[#1e293b] [&_code]:rounded-md [&_code]:px-2 [&_code]:py-1.5 [&_code]:whitespace-pre-wrap [&_code]:break-words">
        <code>
          {instruction.slice(0, 150)}
          {instruction.length > 150 ? '…' : ''}
        </code>
      </div>

      {graph.result_summary && !expanded && (
        <div className="px-3 pb-2.5 text-[0.75rem] text-[#86efac] opacity-90">{graph.result_summary.slice(0, 200)}</div>
      )}

      {expanded && (
        <div id={detailsId} className="border-t border-[#1e293b] px-3 py-2.5 flex flex-col gap-2.5">
          {graph.content_blobs.length === 0 && (
            <div className="text-[0.75rem] text-[#64748b] text-center p-2">No ContentBlob artifacts yet</div>
          )}
          {graph.content_blobs.map((blob) => (
            <div key={blob.blob_id} className="bg-[#0f172a] border border-[#1e293b] rounded-lg px-2.5 py-2">
              <div className="flex gap-2.5 items-center text-[0.72rem] text-[#cbd5e1] mb-1.5">
                <span>Blob #{blob.blob_id}</span>
                <span className="text-[#64748b]">{(blob.content_size / 1000).toFixed(1)}k chars</span>
                {blob.page_count != null && blob.page_count > 0 && (
                  <span className="text-[#64748b]">{blob.page_count} pages</span>
                )}
              </div>
              {blob.ai_summary && <div className="text-[0.78rem] text-[#e2e8f0] leading-[1.45] mb-1.5">{blob.ai_summary}</div>}
              {blob.page_count != null && blob.page_count > 1 && (
                <div className="flex flex-wrap gap-1 mb-1.5">
                  {Array.from({ length: blob.page_count }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={cn(
                        'bg-[#1e293b] border border-[#334155] text-[#94a3b8] rounded px-2 py-0.5 text-[0.68rem] cursor-pointer hover:border-[#a78bfa] hover:text-[#c4b5fd]',
                        activeBlobPage?.blobId === blob.blob_id && activeBlobPage.page === p && 'border-[#a78bfa] text-[#c4b5fd]',
                      )}
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

        </div>
      )}

      <div className="flex gap-2 px-3 py-2 pt-2.5 border-t border-[#1e293b]">
        {graph.callee_thread_id != null && onViewThread && (
          <button
            type="button"
            className="bg-[#1e293b] border border-[#334155] text-[#cbd5e1] rounded-md px-3 py-1 text-[0.72rem] cursor-pointer hover:border-green-500 hover:text-[#86efac]"
            onClick={() => onViewThread(graph.callee_thread_id!)}
          >
            Thread
          </button>
        )}
        {graph.graph_id != null && onViewGraph && (
          <button
            type="button"
            className="bg-[#1e293b] border border-[#334155] text-[#cbd5e1] rounded-md px-3 py-1 text-[0.72rem] cursor-pointer hover:border-green-500 hover:text-[#86efac]"
            onClick={() => onViewGraph(graph.graph_id!)}
          >
            Full Graph
          </button>
        )}
      </div>
    </div>
  );
}

export default SubAgentContainerBlock;
