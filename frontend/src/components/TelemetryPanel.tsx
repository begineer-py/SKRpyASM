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
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          background: '#0f172a',
          borderRight: '1px solid #1e293b',
          overflowY: 'auto',
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '2px solid #1e293b',
            background: '#020617',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: '0.9rem',
              color: '#a78bfa',
              fontWeight: 700,
              letterSpacing: '0.05em',
            }}
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
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#0f172a',
        borderRight: '1px solid #1e293b',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '2px solid #1e293b',
          background: '#020617',
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: '0.9rem',
            color: '#22c55e',
            fontWeight: 700,
            letterSpacing: '0.05em',
            textShadow: '0 0 8px rgba(34, 197, 94, 0.4)',
          }}
        >
          &gt; TELEMETRY
        </h3>
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: '16px', overflowY: 'auto', minWidth: 0 }}>
        {/* Recent Overview Updates */}
        {recentOverviews && recentOverviews.length > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <div
              style={{
                color: '#fbbf24',
                fontSize: '0.75rem',
                fontWeight: 700,
                marginBottom: '10px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              Recent Overview Updates
            </div>
            <div
              style={{
                padding: '10px 12px',
                background: 'rgba(34, 197, 94, 0.05)',
                border: '1px dashed rgba(34, 197, 94, 0.35)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: '#94a3b8',
              }}
            >
              {recentOverviews.slice(0, 2).map((overview: any) => {
                return (
                  <div key={overview.id} style={{ marginBottom: '6px' }}>
                    <span style={{ color: overview.status === 'EXECUTING' ? '#fbbf24' : '#22c55e' }}>
                      {overview.core_target?.name || `Target#${overview.id}`}:
                    </span>{' '}
                    <span style={{ color: '#94a3b8' }}>{overview.status}</span>
                    {(overview.thread_id || overview.parent_thread_id) && (
                      <div style={{ marginTop: 2, color: '#64748b', fontFamily: 'monospace' }}>
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
                                  style={{
                                    marginLeft: 8,
                                    padding: '1px 6px',
                                    fontSize: '0.7rem',
                                    borderRadius: 4,
                                    cursor: 'pointer',
                                    background: 'transparent',
                                    color: '#94a3b8',
                                    border: '1px solid rgba(148, 163, 184, 0.35)',
                                  }}
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
        <div style={{ marginBottom: '24px' }}>
          <div
            style={{
              color: '#fbbf24',
              fontSize: '0.75rem',
              fontWeight: 700,
              marginBottom: '8px',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}
          >
            Response Time
          </div>
          {lastElapsedMs !== null ? (
            <>
              <div
                style={{
                  fontSize: '1.8rem',
                  fontWeight: 700,
                  color:
                    lastElapsedMs > 30000
                      ? '#ef4444'
                      : lastElapsedMs > 15000
                        ? '#f59e0b'
                        : '#10B981',
                  fontFamily: 'monospace',
                  marginBottom: '8px',
                }}
              >
                {lastElapsedMs >= 1000
                  ? `${(lastElapsedMs / 1000).toFixed(1)}s`
                  : `${lastElapsedMs}ms`}
              </div>
              <div
                style={{
                  height: '4px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min((lastElapsedMs / 60000) * 100, 100)}%`,
                    background:
                      lastElapsedMs > 30000
                        ? '#ef4444'
                        : lastElapsedMs > 15000
                          ? '#f59e0b'
                          : '#10B981',
                    borderRadius: '2px',
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </>
          ) : (
            <div style={{ color: '#4b5563', fontSize: '0.8rem' }}>-- Waiting for first message --</div>
          )}
        </div>

        {/* Target Info */}
        {boundTargetId && (
          <div style={{ marginBottom: '24px' }}>
            <div
              style={{
                color: '#fbbf24',
                fontSize: '0.75rem',
                fontWeight: 700,
                marginBottom: '8px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              Bound Target
            </div>
            <div
              style={{
                padding: '8px 12px',
                background: 'rgba(16,185,129,0.1)',
                border: '1px solid rgba(16,185,129,0.3)',
                borderRadius: '4px',
                color: '#34d399',
                fontSize: '0.85rem',
                fontFamily: 'monospace',
              }}
            >
              🎯 ID: {boundTargetId}
            </div>
          </div>
        )}

        {/* Execution Statistics */}
        {execStats.completed + execStats.failed + execStats.running + execStats.pending > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <div
              style={{
                color: '#fbbf24',
                fontSize: '0.75rem',
                fontWeight: 700,
                marginBottom: '12px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              Execution Summary
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '8px',
              }}
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
                  style={{
                    textAlign: 'center',
                    padding: '8px',
                    background: 'rgba(0,0,0,0.3)',
                    borderRadius: '4px',
                    border: `1px solid ${color}30`,
                  }}
                >
                  <div
                    style={{
                      fontSize: '1.2rem',
                      fontWeight: 700,
                      color: color,
                      fontFamily: 'monospace',
                    }}
                  >
                    {count}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: '#6b7280', fontFamily: 'monospace' }}>
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
              style={{
                color: '#fbbf24',
                fontSize: '0.75rem',
                fontWeight: 700,
                marginBottom: '12px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
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
