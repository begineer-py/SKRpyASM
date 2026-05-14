/**
 * StepLogViewer Component
 * 
 * Displays real-time Step execution logs with color-coded levels and tags.
 * Includes auto-scrolling, filtering, and compact/expanded views.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useStepLogStream, StepLog } from '../hooks/useStepLogStream';
import './StepLogViewer.css';

interface StepLogViewerProps {
  /** Step ID to stream logs for */
  stepId: number | null;
  
  /** Whether to auto-scroll to latest log (default: true) */
  autoScroll?: boolean;
  
  /** Maximum number of logs to display (default: 1000) */
  maxLogs?: number;
  
  /** Compact view mode (default: false) */
  compact?: boolean;
  
  /** Callback when logs are updated */
  onLogsUpdate?: (logs: StepLog[]) => void;
}

/**
 * Color mapping for log levels
 */
const LEVEL_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  INFO: { bg: '#e0f2fe', text: '#0369a1', label: 'ℹ️' },
  DEBUG: { bg: '#f0fdf4', text: '#16a34a', label: '🐛' },
  WARN: { bg: '#fef3c7', text: '#b45309', label: '⚠️' },
  ERROR: { bg: '#fee2e2', text: '#dc2626', label: '❌' },
  AI_THOUGHT: { bg: '#e9d5ff', text: '#7c3aed', label: '💭' },
  ACTION: { bg: '#dbeafe', text: '#2563eb', label: '▶️' },
  RESULT: { bg: '#dcfce7', text: '#059669', label: '✓' },
};

/**
 * Color mapping for tags
 */
const TAG_COLORS: Record<string, string> = {
  SKILL_EXEC: '#8b5cf6',
  COMMAND: '#ec4899',
  API_CALL: '#06b6d4',
  SCAN: '#f97316',
  PARSE: '#6366f1',
  DECISION: '#d946ef',
  ERROR_HANDLING: '#ef4444',
  STATE_UPDATE: '#14b8a6',
  CHECKPOINT: '#6b7280',
};

export function StepLogViewer({
  stepId,
  autoScroll = true,
  maxLogs = 1000,
  compact = false,
  onLogsUpdate,
}: StepLogViewerProps) {
  const { logs, isConnected, error, lastSequence } = useStepLogStream(stepId);
  const [filter, setFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string[]>([]);
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Limit logs to maxLogs
  const displayLogs = logs.slice(-maxLogs);

  // Apply filters
  const filteredLogs = displayLogs.filter((log) => {
    if (levelFilter.length > 0 && !levelFilter.includes(log.level)) {
      return false;
    }
    if (filter && !log.message.toLowerCase().includes(filter.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Auto-scroll to latest log
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  // Callback when logs update
  useEffect(() => {
    onLogsUpdate?.(displayLogs);
  }, [displayLogs, onLogsUpdate]);

  const levelColor = (level: string) => LEVEL_COLORS[level] || LEVEL_COLORS.INFO;
  const tagColor = (tag: string) => TAG_COLORS[tag] || '#9ca3af';

  const toggleLogExpansion = (logId: number) => {
    setExpandedLogId(expandedLogId === logId ? null : logId);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className={`step-log-viewer ${compact ? 'compact' : ''}`}>
      {/* Header */}
      <div className="slv-header">
        <div className="slv-title">
          <h3>📋 STEP EXECUTION LOGS</h3>
          <span className="slv-badge">{filteredLogs.length} / {displayLogs.length}</span>
        </div>
        <div className="slv-status">
          <span className={`slv-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🔴 LIVE' : '⚫ OFFLINE'}
          </span>
          <span className="slv-sequence">seq#{lastSequence}</span>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="slv-error">
          <span>⚠️ {error.message}</span>
        </div>
      )}

      {/* Controls */}
      <div className="slv-controls">
        <input
          type="text"
          placeholder="Search logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="slv-search"
        />
        
        <div className="slv-level-filter">
          {Object.entries(LEVEL_COLORS).map(([level]) => (
            <label key={level} className="slv-filter-label" title={level}>
              <input
                type="checkbox"
                checked={levelFilter.includes(level) || levelFilter.length === 0}
                onChange={(e) => {
                  if (e.target.checked) {
                    setLevelFilter(levelFilter.length === Object.keys(LEVEL_COLORS).length - 1
                      ? []
                      : [...levelFilter.filter(l => l !== level)].filter(l => l !== level)
                    );
                  } else {
                    setLevelFilter([...levelFilter.filter(l => l !== level), level]);
                  }
                }}
              />
              <span style={{ color: levelColor(level).text }}>
                {levelColor(level).label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Logs Container */}
      <div className="slv-logs-container">
        {filteredLogs.length === 0 ? (
          <div className="slv-empty">
            {logs.length === 0 ? '⏳ Waiting for logs...' : '🔍 No logs match filter'}
          </div>
        ) : (
          filteredLogs.map((log) => {
            const isExpanded = expandedLogId === log.id;
            const colors = levelColor(log.level);
            
            return (
              <div
                key={log.id}
                className="slv-log-entry"
                style={{ borderLeftColor: colors.text }}
              >
                <div
                  className="slv-log-header"
                  onClick={() => toggleLogExpansion(log.id)}
                  style={{ cursor: 'pointer', backgroundColor: colors.bg }}
                >
                  <div className="slv-log-meta">
                    <span className="slv-level" title={log.level}>
                      {colors.label}
                    </span>
                    <span
                      className="slv-tag"
                      style={{
                        backgroundColor: tagColor(log.tag),
                        color: '#fff',
                      }}
                    >
                      {log.tag}
                    </span>
                    {log.action_status && (
                      <span className="slv-status-badge">
                        {log.action_status}
                      </span>
                    )}
                    {log.execution_time_ms && (
                      <span className="slv-timing">
                        {log.execution_time_ms}ms
                      </span>
                    )}
                  </div>
                  
                  <div className="slv-log-message">
                    {log.message.substring(0, compact ? 100 : 200)}
                    {log.message.length > (compact ? 100 : 200) && '...'}
                  </div>
                  
                  <div className="slv-log-time">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </div>
                </div>

                {/* Expanded view */}
                {isExpanded && (
                  <div className="slv-log-details">
                    <div className="slv-details-content">
                      <p className="slv-full-message">{log.message}</p>
                      
                      <div className="slv-metadata">
                        <div>
                          <strong>ID:</strong> {log.id}
                        </div>
                        <div>
                          <strong>Sequence:</strong> {log.sequence}
                        </div>
                        <div>
                          <strong>Level:</strong> {log.level}
                        </div>
                        <div>
                          <strong>Tag:</strong> {log.tag}
                        </div>
                        {log.action_status && (
                          <div>
                            <strong>Status:</strong> {log.action_status}
                          </div>
                        )}
                        {log.execution_time_ms && (
                          <div>
                            <strong>Duration:</strong> {log.execution_time_ms}ms
                          </div>
                        )}
                        <div>
                          <strong>Timestamp:</strong>{' '}
                          {new Date(log.created_at).toLocaleString()}
                        </div>
                      </div>

                      <button
                        className="slv-copy-btn"
                        onClick={() =>
                          copyToClipboard(
                            `[${log.level}] ${log.tag}: ${log.message}`
                          )
                        }
                      >
                        📋 Copy
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}

export default StepLogViewer;
