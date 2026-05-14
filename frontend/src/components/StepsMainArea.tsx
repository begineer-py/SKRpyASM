/**
 * StepsMainArea Component
 * 
 * Main content area showing step execution details and logs.
 * Part of P11 redesigned AICenterPage layout (Sidebar + Main Content).
 */

import React, { useMemo } from 'react';
import { StepLogViewer } from './StepLogViewer';

interface Step {
  id: number;
  status: 'COMPLETED' | 'FAILED' | 'RUNNING' | 'PENDING';
  note?: { content: string };
  core_attackvectors?: Array<{ name: string }>;
}

interface StepsMainAreaProps {
  /** Current step ID for streaming logs */
  selectedStepId?: number | null;
  
  /** Steps array from GraphQL */
  steps?: Step[];
  
  /** Whether to show the log viewer */
  showLogs?: boolean;
  
  /** Callback when a step is selected */
  onStepSelect?: (stepId: number) => void;
}

export function StepsMainArea({
  selectedStepId = null,
  steps = [],
  showLogs = true,
  onStepSelect,
}: StepsMainAreaProps) {
  const recentSteps = useMemo(() => steps.slice(-20), [steps]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#0f172a',
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
          &gt; EXECUTION ANALYSIS
        </h3>
      </div>

      {/* Content - Split between list and logs */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* Left: Step list */}
        <div
          style={{
            flex: '0 0 40%',
            borderRight: '1px solid #1e293b',
            overflowY: 'auto',
            padding: '12px',
          }}
        >
          {recentSteps.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentSteps.map((step) => {
                const name = step.core_attackvectors?.[0]?.name || step.note?.content || `Step #${step.id}`;
                const statusColor =
                  step.status === 'COMPLETED'
                    ? '#10B981'
                    : step.status === 'FAILED'
                      ? '#ef4444'
                      : step.status === 'RUNNING'
                        ? '#fbbf24'
                        : '#6b7280';

                const isSelected = selectedStepId === step.id;

                return (
                  <div
                    key={step.id}
                    onClick={() => onStepSelect?.(step.id)}
                    style={{
                      padding: '10px 12px',
                      background: isSelected ? 'rgba(34, 197, 94, 0.1)' : 'rgba(0,0,0,0.2)',
                      border: isSelected ? '1px solid #22c55e' : '1px solid transparent',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '0.8rem',
                      fontFamily: 'monospace',
                    }}
                    title={name}
                  >
                    <div
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: statusColor,
                        flexShrink: 0,
                        boxShadow:
                          step.status === 'RUNNING'
                            ? `0 0 6px ${statusColor}`
                            : 'none',
                      }}
                    />
                    <div
                      style={{
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        color: '#94a3b8',
                      }}
                    >
                      {name}
                    </div>
                    <div style={{ color: statusColor, flexShrink: 0, fontSize: '0.7rem' }}>
                      {step.status[0]}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ color: '#4b5563', fontSize: '0.8rem', textAlign: 'center', marginTop: '20px' }}>
              No steps executed yet
            </div>
          )}
        </div>

        {/* Right: Log viewer or placeholder */}
        <div
          style={{
            flex: '0 0 60%',
            overflowY: 'auto',
            background: '#0a0f1f',
          }}
        >
          {showLogs && selectedStepId ? (
            <StepLogViewer stepId={selectedStepId} />
          ) : (
            <div
              style={{
                padding: '20px',
                color: '#4b5563',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
              }}
            >
              {selectedStepId ? (
                <span>Loading logs...</span>
              ) : recentSteps.length > 0 ? (
                <span>👈 Select a step to view its execution logs</span>
              ) : (
                <span>No execution data available</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
