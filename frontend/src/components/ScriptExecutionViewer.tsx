/**
 * ScriptExecutionViewer Component
 * 
 * 顯示與特定 Step 關聯的所有腳本執行歷史
 * 支持查看：
 * - 執行狀態 (SUCCESS/FAILED/TIMEOUT)
 * - 輸入/輸出驗證狀態
 * - 執行耗時
 * - 輸入輸出 JSON 預覽
 * - 錯誤信息診斷
 */

import { useState, useEffect } from 'react';
import { useHasuraQuery } from '../hooks/useHasuraQuery';
import { GET_SCRIPT_EXECUTIONS } from '../queries';
import './ScriptExecutionViewer.css';

interface ScriptExecution {
  id: number;
  skill?: {
    id: number;
    name: string;
    version: number;
    is_robust: boolean;
  } | null;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'TIMEOUT';
  validation_status: 'NOT_VALIDATED' | 'INPUT_INVALID' | 'OUTPUT_INVALID' | 'VALIDATED' | 'VALIDATION_ERROR';
  script_language: 'python' | 'bash';
  args_string?: string;
  input_json?: Record<string, any> | null;
  output_json?: Record<string, any> | null;
  raw_output?: string;
  exit_code?: number | null;
  error_message?: string;
  validation_error?: string;
  execution_duration_ms?: number | null;
  started_at: string;
  completed_at?: string | null;
  attack_vector?: {
    id: number;
    name: string;
  } | null;
}

interface ScriptExecutionViewerProps {
  /** Step ID to fetch script executions for */
  stepId: number | null;
  
  /** Callback when executions are loaded */
  onExecutionsLoaded?: (executions: ScriptExecution[]) => void;
  
  /** Compact view mode */
  compact?: boolean;
}

const STATUS_COLORS: Record<string, { bg: string; text: string; badge: string }> = {
  SUCCESS: { bg: '#dcfce7', text: '#059669', badge: '✓' },
  FAILED: { bg: '#fee2e2', text: '#dc2626', badge: '✗' },
  RUNNING: { bg: '#dbeafe', text: '#2563eb', badge: '⟳' },
  PENDING: { bg: '#f3f4f6', text: '#6b7280', badge: '⏳' },
  TIMEOUT: { bg: '#fed7aa', text: '#d97706', badge: '⏱️' },
};

const VALIDATION_COLORS: Record<string, { bg: string; text: string }> = {
  VALIDATED: { bg: '#d1fae5', text: '#065f46' },
  NOT_VALIDATED: { bg: '#f3f4f6', text: '#6b7280' },
  INPUT_INVALID: { bg: '#fecaca', text: '#7f1d1d' },
  OUTPUT_INVALID: { bg: '#fecaca', text: '#7f1d1d' },
  VALIDATION_ERROR: { bg: '#fed7aa', text: '#92400e' },
};

export default function ScriptExecutionViewer({
  stepId,
  onExecutionsLoaded,
  compact = false,
}: ScriptExecutionViewerProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  
  // Use Hasura query hook only when stepId is available
  const { data, loading, error } = useHasuraQuery(
    GET_SCRIPT_EXECUTIONS,
    stepId ? { stepId } : {}
  );

  const executions: ScriptExecution[] = stepId && data?.core_script_execution ? data.core_script_execution : [];

  // Notify parent when executions are loaded
  useEffect(() => {
    onExecutionsLoaded?.(executions);
  }, [executions, onExecutionsLoaded]);

  if (!stepId) {
    return (
      <div className="script-execution-viewer empty">
        <p>Select a step to view script executions</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="script-execution-viewer loading">
        <div className="spinner"></div>
        <p>Loading script executions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="script-execution-viewer error">
        <p>❌ Error: {error instanceof Error ? error.message : String(error)}</p>
      </div>
    );
  }

  if (executions.length === 0) {
    return (
      <div className="script-execution-viewer empty">
        <p>No script executions for this step</p>
      </div>
    );
  }

  return (
    <div className={`script-execution-viewer ${compact ? 'compact' : 'expanded'}`}>
      <h3>Script Executions ({executions.length})</h3>
      
      <div className="execution-list">
        {executions.map((exec) => (
          <div
            key={exec.id}
            className={`execution-item ${expandedId === exec.id ? 'expanded' : ''}`}
          >
            {/* Header */}
            <div
              className="execution-header"
              onClick={() => setExpandedId(expandedId === exec.id ? null : exec.id)}
            >
              {/* Status Badge */}
              <div
                className="status-badge"
                style={{
                  backgroundColor: STATUS_COLORS[exec.status].bg,
                  color: STATUS_COLORS[exec.status].text,
                }}
              >
                {STATUS_COLORS[exec.status].badge} {exec.status}
              </div>

              {/* Skill Name or "Temporary" */}
              <div className="skill-info">
                {exec.skill ? (
                  <span className="skill-name">
                    {exec.skill.name}
                    <span className={`version ${exec.skill.is_robust ? 'robust' : ''}`}>
                      v{exec.skill.version}
                      {exec.skill.is_robust && ' 🛡️'}
                    </span>
                  </span>
                ) : (
                  <span className="skill-name temporary">Temporary Script</span>
                )}
              </div>

              {/* Validation Status */}
              {exec.validation_status !== 'NOT_VALIDATED' && (
                <div
                  className="validation-badge"
                  style={{
                    backgroundColor: VALIDATION_COLORS[exec.validation_status].bg,
                    color: VALIDATION_COLORS[exec.validation_status].text,
                  }}
                >
                  {exec.validation_status === 'VALIDATED' && '✓'}
                  {exec.validation_status === 'INPUT_INVALID' && '✗ Input'}
                  {exec.validation_status === 'OUTPUT_INVALID' && '✗ Output'}
                  {exec.validation_status === 'VALIDATION_ERROR' && '⚠️ Error'}
                </div>
              )}

              {/* Duration */}
              {exec.execution_duration_ms && (
                <div className="duration">
                  ⏱️ {exec.execution_duration_ms}ms
                </div>
              )}

              {/* Timestamp */}
              <div className="timestamp">
                {new Date(exec.started_at).toLocaleTimeString()}
              </div>

              {/* Expand Icon */}
              <div className="expand-icon">
                {expandedId === exec.id ? '▼' : '▶'}
              </div>
            </div>

            {/* Expanded Content */}
            {expandedId === exec.id && (
              <div className="execution-details">
                {/* Arguments */}
                {exec.args_string && (
                  <div className="detail-section">
                    <h4>Arguments</h4>
                    <code>{exec.args_string}</code>
                  </div>
                )}

                {/* Language */}
                <div className="detail-section">
                  <h4>Language</h4>
                  <code>{exec.script_language}</code>
                </div>

                {/* Exit Code */}
                {exec.exit_code !== null && exec.exit_code !== undefined && (
                  <div className="detail-section">
                    <h4>Exit Code</h4>
                    <code style={{ color: exec.exit_code === 0 ? '#059669' : '#dc2626' }}>
                      {exec.exit_code}
                    </code>
                  </div>
                )}

                {/* Input JSON */}
                {exec.input_json && (
                  <div className="detail-section">
                    <h4>Input</h4>
                    <pre>{JSON.stringify(exec.input_json, null, 2)}</pre>
                  </div>
                )}

                {/* Output JSON */}
                {exec.output_json && (
                  <div className="detail-section">
                    <h4>Output (Structured)</h4>
                    <pre>{JSON.stringify(exec.output_json, null, 2)}</pre>
                  </div>
                )}

                {/* Raw Output */}
                {exec.raw_output && (
                  <div className="detail-section">
                    <h4>Raw Output</h4>
                    <pre className="raw-output">{exec.raw_output}</pre>
                  </div>
                )}

                {/* Error Message */}
                {exec.error_message && (
                  <div className="detail-section error">
                    <h4>Error</h4>
                    <pre>{exec.error_message}</pre>
                  </div>
                )}

                {/* Validation Error */}
                {exec.validation_error && (
                  <div className="detail-section error">
                    <h4>Validation Error</h4>
                    <pre>{exec.validation_error}</pre>
                  </div>
                )}

                {/* Attack Vector */}
                {exec.attack_vector && (
                  <div className="detail-section">
                    <h4>Attack Vector</h4>
                    <a href={`/attack-vectors/${exec.attack_vector.id}`}>
                      {exec.attack_vector.name}
                    </a>
                  </div>
                )}

                {/* Promotion Suggestion */}
                {exec.status === 'SUCCESS' && 
                 exec.validation_status === 'VALIDATED' && 
                 !exec.skill && (
                  <div className="detail-section suggestion">
                    <h4>💡 Ready for Promotion</h4>
                    <p>
                      This script executed successfully and passed validation.
                      Consider promoting it to a reusable skill using:
                    </p>
                    <code>promote_successful_script(script_execution_id={exec.id}, skill_name="...")</code>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
