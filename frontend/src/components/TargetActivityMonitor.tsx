/**
 * TargetActivityMonitor Component
 * 
 * 顯示特定 Target 的所有 AI 活動，不依賴 Overview 的存在
 * 支持：
 * - 實時步驟監控（無論是否有 Overview）
 * - 臨時執行跟蹤
 * - 腳本執行歷史
 * - 操作進度可視化
 */

import { useState } from 'react';
import { useHasuraSubscription } from '../hooks/useHasuraSubscription';
import { SUBSCRIBE_TARGET_STEPS } from '../queries';
import './TargetActivityMonitor.css';

interface StepNote {
  content?: string;
  ai_thoughts?: string;
}

interface Overview {
  id: number;
  status: string;
  summary?: string;
  risk_score: number;
  created_at: string;
  updated_at: string;
}

interface TargetStep {
  id: number;
  status: string;
  operation_type?: string;
  created_at: string;
  completed_at?: string;
  overview_id?: number;
  overview?: Overview;
  core_stepnote?: StepNote;
  script_executions?: Array<{
    id: number;
    status: string;
    validation_status: string;
    script_language: string;
    started_at: string;
  }>;
}

interface TargetActivityMonitorProps {
  targetId: number | null;
  compact?: boolean;
  maxSteps?: number;
}

const STATUS_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  PENDING: { bg: '#f3f4f6', text: '#6b7280', icon: '⏳' },
  RUNNING: { bg: '#dbeafe', text: '#2563eb', icon: '⟳' },
  COMPLETED: { bg: '#dcfce7', text: '#059669', icon: '✓' },
  FAILED: { bg: '#fee2e2', text: '#dc2626', icon: '✗' },
  WAITING_FOR_ASYNC: { bg: '#fef3c7', text: '#92400e', icon: '⏸️' },
  ENDED: { bg: '#e5e7eb', text: '#374151', icon: '■' },
};

const OPERATION_LABELS: Record<string, string> = {
  AI_AUTOMATION_EXECUTION: '🤖 AI 自動化',
  MANUAL_TEST: '👤 手動測試',
  SCAN_OPERATION: '🔍 掃描操作',
  ANALYSIS: '📊 分析',
  EXPLOITATION: '💣 利用',
  RECON: '🕵️ 偵察',
};

export default function TargetActivityMonitor({
  targetId,
  compact = false,
  maxSteps = 20,
}: TargetActivityMonitorProps) {
  const [expandedStepId, setExpandedStepId] = useState<number | null>(null);

  // Use subscription hook to get real-time updates
  const { data, loading, error } = useHasuraSubscription(
    SUBSCRIBE_TARGET_STEPS,
    targetId ? { targetId } : {}
  );

  const steps: TargetStep[] = targetId && data?.core_overview ? 
    data.core_overview
      .flatMap((overview: any) => 
        (overview.core_steps || []).map((step: any) => ({
          ...step,
          overview: { id: overview.id, status: overview.status, summary: overview.summary, risk_score: overview.risk_score }
        }))
      )
      .sort((a: TargetStep, b: TargetStep) => {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        return bTime - aTime; // DESC
      })
      .slice(0, maxSteps)
    : [];

  if (!targetId) {
    return (
      <div className="target-activity-monitor empty">
        <p>Select a target to view activity</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="target-activity-monitor loading">
        <div className="spinner"></div>
        <p>Loading target activity...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="target-activity-monitor error">
        <p>❌ Error: {error instanceof Error ? error.message : String(error)}</p>
      </div>
    );
  }

  if (steps.length === 0) {
    return (
      <div className="target-activity-monitor empty">
        <p>No activity yet. AI will start execution automatically.</p>
      </div>
    );
  }

  // Calculate activity summary
  const activeSteps = steps.filter(s => s.status === 'RUNNING' || s.status === 'PENDING');
  const completedSteps = steps.filter(s => s.status === 'COMPLETED');
  const failedSteps = steps.filter(s => s.status === 'FAILED');

  return (
    <div className={`target-activity-monitor ${compact ? 'compact' : 'expanded'}`}>
      {/* Header with summary */}
      <div className="activity-header">
        <h3>AI Activity Monitor</h3>
        <div className="activity-stats">
          {activeSteps.length > 0 && (
            <span className="stat active">
              <span className="dot"></span>
              {activeSteps.length} Running
            </span>
          )}
          <span className="stat completed">✓ {completedSteps.length}</span>
          {failedSteps.length > 0 && <span className="stat failed">✗ {failedSteps.length}</span>}
          <span className="stat total">Total: {steps.length}</span>
        </div>
      </div>

      {/* Activity timeline */}
      <div className="activity-timeline">
        {steps.map((step, idx) => {
          const statusColor = STATUS_COLORS[step.status] || STATUS_COLORS.PENDING;
          const isExpanded = expandedStepId === step.id;
          const duration = step.completed_at
            ? Math.round(
                (new Date(step.completed_at).getTime() - new Date(step.created_at).getTime()) /
                  1000
              )
            : null;

          return (
            <div key={step.id} className={`activity-item ${isExpanded ? 'expanded' : ''}`}>
              {/* Timeline point */}
              <div className="timeline-point">
                <div
                  className="point"
                  style={{ backgroundColor: statusColor.bg, borderColor: statusColor.text }}
                >
                  {statusColor.icon}
                </div>
                {idx < steps.length - 1 && <div className="line"></div>}
              </div>

              {/* Step content */}
              <div className="activity-content">
                {/* Header */}
                <div
                  className="activity-item-header"
                  onClick={() => setExpandedStepId(isExpanded ? null : step.id)}
                >
                  {/* Operation type badge */}
                  <span className="operation-badge">
                    {OPERATION_LABELS[step.operation_type || 'AI_AUTOMATION_EXECUTION'] ||
                      step.operation_type ||
                      '⚙️ Operation'}
                  </span>

                  {/* Status badge */}
                  <span
                    className="status-badge"
                    style={{ backgroundColor: statusColor.bg, color: statusColor.text }}
                  >
                    {step.status}
                  </span>

                  {/* Overview link if available */}
                  {step.overview && (
                    <a
                      href={`/overviews/${step.overview.id}`}
                      className="overview-link"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Overview #{step.overview.id}
                    </a>
                  )}

                  {/* Duration */}
                  {duration && <span className="duration">⏱️ {duration}s</span>}

                  {/* Timestamp */}
                  <span className="timestamp">
                    {new Date(step.created_at).toLocaleTimeString()}
                  </span>

                  {/* Expand icon */}
                  <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                </div>

                {/* Summary (always visible) */}
                {step.core_stepnote?.content && (
                  <div className="step-summary">
                    {step.core_stepnote.content.split('\n')[0]}
                  </div>
                )}

                {/* Expanded details */}
                {isExpanded && (
                  <div className="activity-details">
                    {/* Full note */}
                    {step.core_stepnote?.content && (
                      <div className="detail-section">
                        <h4>Summary</h4>
                        <p style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                          {step.core_stepnote.content}
                        </p>
                      </div>
                    )}

                    {/* AI Thoughts */}
                    {step.core_stepnote?.ai_thoughts && (
                      <div className="detail-section">
                        <h4>AI Thoughts</h4>
                        <p style={{ whiteSpace: 'pre-wrap', fontSize: '12px', color: '#7c3aed' }}>
                          💭 {step.core_stepnote.ai_thoughts}
                        </p>
                      </div>
                    )}

                    {/* Overview details */}
                    {step.overview && (
                      <div className="detail-section overview-section">
                        <h4>Overview Context</h4>
                        <div>
                          <div>
                            <strong>Status:</strong> {step.overview.status}
                          </div>
                          <div>
                            <strong>Risk Score:</strong> {step.overview.risk_score}
                          </div>
                          {step.overview.summary && (
                            <div>
                              <strong>Summary:</strong>
                              <p style={{ fontSize: '12px', marginTop: '4px' }}>
                                {step.overview.summary.substring(0, 150)}...
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="detail-section actions">
                      <a
                        href={`/execution-monitor?step=${step.id}`}
                        className="action-link"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        View Full Details
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="activity-footer">
        <p style={{ fontSize: '11px', color: '#9ca3af' }}>
          Showing {steps.length} of recent activities. Auto-refreshes in real-time.
        </p>
      </div>
    </div>
  );
}
