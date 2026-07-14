/**
 * TelemetryPanel Component
 * 
 * Sidebar showing LLM metrics, execution summary, and waveform chart.
 * Part of P11 redesigned AICenterPage layout (Sidebar + Main Content).
 */

import { useMemo } from 'react';
import { WaveformChart } from './WaveformChart';
import { TutorialPanel } from './TutorialPanel';

interface ExecutionSample {
  id: number;
  status: 'COMPLETED' | 'FAILED' | 'RUNNING' | 'PENDING';
  estimated_duration_ms?: number;
  name?: string;
}

interface TelemetryPanelProps {
  /** LLM response time in milliseconds */
  lastElapsedMs?: number | null;
  
  /** Execution samples for visualization */
  samples?: ExecutionSample[];

  /** Optional recent overview updates */
  recentOverviews?: Array<any>;

  /** Map thread_id -> display name for provenance */
  threadNameById?: Record<string, string>;

  /** Jump to a main chat thread (forces MAIN view) */
  onOpenThread?: (threadId: string) => void;
  
  /** Bound target ID */
  boundTargetId?: number | null;
  
  /** View mode for tutorial context */
  viewMode?: 'MAIN' | 'AUTO';
  
  /** Whether any data has been loaded yet */
  hasData?: boolean;
}

export function TelemetryPanel({
  lastElapsedMs = null,
  samples = [],
  recentOverviews = [],
  threadNameById = {},
  onOpenThread,
  boundTargetId = null,
  viewMode = 'MAIN',
  hasData = false,
}: TelemetryPanelProps) {
  // Compute step statistics and timings for chart
  const execStats = useMemo(() => {
    if (!samples || samples.length === 0) {
      return {
        completed: 0,
        failed: 0,
        running: 0,
        pending: 0,
        chartData: [],
      };
    }

    const chartData = samples
      .slice(-12)
      .map((s) => ({
        id: s.id,
        name:
          s.name ||
          `Execution #${s.id}`,
        duration_ms: s.estimated_duration_ms || 0,
        status: s.status,
      }));

    return {
      completed: samples.filter((s) => s.status === 'COMPLETED').length,
      failed: samples.filter((s) => s.status === 'FAILED').length,
      running: samples.filter((s) => s.status === 'RUNNING').length,
      pending: samples.filter((s) => s.status === 'PENDING').length,
      chartData,
    };
  }, [samples]);

  // Show tutorial if no data
  if (!hasData) {
    return (
      <div
        className="flex flex-col h-full bg-[#0f172a] border-r border-border-subtle overflow-y-auto"
      >
        <div
          className="px-5 py-4 border-b-2 border-border-subtle bg-[#020617]"
        >
          <h3
            className="m-0 text-[0.9rem] text-purple font-bold tracking-wider"
          >
            ⚙️ SYSTEM GUIDE
          </h3>
        </div>
        <TutorialPanel viewMode={viewMode} />
      </div>
    );
  }

  // Normal data view
  return (
    <div
      className="flex flex-col h-full bg-[#0f172a] border-r border-border-subtle overflow-y-auto"
    >
      {/* Header */}
      <div
        className="px-5 py-4 border-b-2 border-border-subtle bg-[#020617]"
      >
        <h3
          className="m-0 text-[0.9rem] text-green font-bold tracking-wider"
          style={{ textShadow: '0 0 8px rgba(34, 197, 94, 0.4)' }}
        >
          &gt; TELEMETRY
        </h3>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 overflow-y-auto min-w-0">
        {/* Recent Overview Updates */}
        {recentOverviews && recentOverviews.length > 0 && (
          <div className="mb-6">
            <div
              className="text-amber text-xs font-bold mb-[10px] tracking-wider uppercase"
            >
              Recent Overview Updates
            </div>
            <div
              className="px-3 py-[10px] bg-[rgba(34,197,94,0.05)] border border-dashed border-[rgba(34,197,94,0.35)] rounded-md text-xs text-text-secondary"
            >
              {recentOverviews.slice(0, 2).map((overview: any) => {
                return (
                  <div key={overview.id} className="mb-1.5">
                    <span style={{ color: overview.status === 'EXECUTING' ? '#fbbf24' : '#22c55e' }}>
                      {overview.core_target?.name || `Target#${overview.id}`}:
                    </span>{' '}
                    <span className="text-text-secondary">{overview.status}</span>
                    {(overview.thread_id || overview.parent_thread_id) && (
                      <div className="mt-0.5 text-text-muted font-mono">
                        {(() => {
                          const originId = overview.parent_thread_id ?? overview.thread_id;
                          const originKey = originId != null ? String(originId) : null;
                          const originName = originKey ? threadNameById[originKey] : null;

                          return (
                            <>
                              <span>
                                origin: {originName ? `${originName} ` : ''}({originKey ?? '—'})
                              </span>
                              {originKey && onOpenThread && (
                                <button
                                  onClick={() => onOpenThread(originKey)}
                                  className="ml-2 px-1.5 py-px text-[0.7rem] rounded cursor-pointer bg-transparent text-text-secondary border border-border-subtle"
                                  title="Open originating chat thread"
                                >
                                  Open chat
                                </button>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* LLM Response Time */}
        <div className="mb-6">
          <div
            className="text-amber text-xs font-bold mb-2 tracking-wider uppercase"
          >
            Response Time
          </div>
          {lastElapsedMs !== null ? (
            <>
              <div
                className="text-[1.8rem] font-bold font-mono mb-2"
                style={{
                  color:
                    lastElapsedMs > 30000
                      ? '#ef4444'
                      : lastElapsedMs > 15000
                        ? '#f59e0b'
                        : '#10B981',
                }}
              >
                {lastElapsedMs >= 1000
                  ? `${(lastElapsedMs / 1000).toFixed(1)}s`
                  : `${lastElapsedMs}ms`}
              </div>
              <div
                className="h-1 bg-[rgba(255,255,255,0.1)] rounded-sm overflow-hidden"
              >
                <div
                  className="h-full rounded-sm"
                  style={{
                    width: `${Math.min((lastElapsedMs / 60000) * 100, 100)}%`,
                    background:
                      lastElapsedMs > 30000
                        ? '#ef4444'
                        : lastElapsedMs > 15000
                          ? '#f59e0b'
                          : '#10B981',
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </>
          ) : (
            <div className="text-text-muted text-[0.8rem]">-- Waiting for first message --</div>
          )}
        </div>

        {/* Target Info */}
        {boundTargetId && (
          <div className="mb-6">
            <div
              className="text-amber text-xs font-bold mb-2 tracking-wider uppercase"
            >
              Bound Target
            </div>
            <div
              className="px-3 py-2 bg-[rgba(16,185,129,0.1)] border border-[rgba(16,185,129,0.3)] rounded text-green text-[0.85rem] font-mono"
            >
              🎯 ID: {boundTargetId}
            </div>
          </div>
        )}

        {/* Execution Statistics */}
        {execStats.completed + execStats.failed + execStats.running + execStats.pending > 0 && (
          <div className="mb-6">
            <div
              className="text-amber text-xs font-bold mb-3 tracking-wider uppercase"
            >
              Execution Summary
            </div>
            <div
              className="grid grid-cols-2 gap-2"
            >
              {(
                [
                  ['DONE', execStats.completed, '#10B981'],
                  ['FAIL', execStats.failed, '#ef4444'],
                  ['RUN', execStats.running, '#fbbf24'],
                  ['WAIT', execStats.pending, '#6b7280'],
                ] as Array<[string, number, string]>
              ).map(([label, count, color]) => (
                <div
                  key={label}
                  className="text-center p-2 bg-[rgba(0,0,0,0.3)] rounded border border-solid"
                  style={{ borderColor: `${color}30` }}
                >
                  <div
                    className="text-[1.2rem] font-bold font-mono"
                    style={{ color }}
                  >
                    {count}
                  </div>
                  <div className="text-[0.65rem] text-text-muted font-mono">
                    {label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Execution Duration Waveform */}
        {execStats.chartData.length > 0 && (
          <div>
            <div
              className="text-amber text-xs font-bold mb-3 tracking-wider uppercase"
            >
              Duration Chart
            </div>
            <WaveformChart samples={execStats.chartData} height={100} />
          </div>
        )}
      </div>
    </div>
  );
}
