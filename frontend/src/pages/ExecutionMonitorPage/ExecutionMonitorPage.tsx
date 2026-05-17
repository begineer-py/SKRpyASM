import { useState, useMemo, useCallback, useEffect } from 'react';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { GET_ALL_EXECUTION_STEPS } from '../../queries';
import StepLogViewer from '../../components/StepLogViewer';
import { StepService } from '../../services/stepService';
import { OverviewService } from '../../services/overviewService';
import { assistantApi } from '../../services/assistantApi';
import './ExecutionMonitor.css';

interface Step {
  id: number;
  status: string;
  created_at: string;
  completed_at?: string | null;
  core_stepnote?: {
    id: number;
    content: string;
    ai_thoughts?: string;
    created_at: string;
  };
  core_attackvectors?: Array<{
    id: number;
    name: string;
    description?: string;
    vector_type?: string;
    created_at: string;
  }>;
}

interface Overview {
  id: number;
  status: string;
  risk_score: number;
  summary?: string;
  business_impact?: string;
  plan?: any;
  knowledge?: any;
  techs?: any;
  created_at: string;
  updated_at: string;
  thread_id?: number | null;
  parent_thread_id?: number | null;
  core_target: {
    id: number;
    name: string;
    description?: string;
  };
  core_steps?: Step[];
}

export default function ExecutionMonitorPage() {
  const { data, loading, error } = useHasuraSubscription(GET_ALL_EXECUTION_STEPS);

  // Thread id -> name mapping for provenance display.
  const [threadNameById, setThreadNameById] = useState<Record<string, string>>({});
  
  // Filter states
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [timeRangeFilter, setTimeRangeFilter] = useState<'all' | '1h' | '24h' | '7d'>('all');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'duration' | 'success_rate'>('updated');
  
  // State for expanded overview items
  const [expandedOverviews, setExpandedOverviews] = useState<Set<number>>(new Set());

  // State for selected step to view logs
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);

  // Right panel StepNote editor state (human-facing summary)
  const [isEditingNote, setIsEditingNote] = useState(false);
  const [editNoteContent, setEditNoteContent] = useState<string>('');
  const [isSavingNote, setIsSavingNote] = useState(false);
  const [noteSaveError, setNoteSaveError] = useState<string | null>(null);

  // Overview editing state
  const [editingOverviewId, setEditingOverviewId] = useState<number | null>(null);
  const [editOverviewFields, setEditOverviewFields] = useState<{
    status: string;
    summary: string;
    risk_score: number;
    business_impact: string;
    plan: string;
    knowledge: string;
  }>({ status: '', summary: '', risk_score: 0, business_impact: '', plan: '', knowledge: '' });
  const [isSavingOverview, setIsSavingOverview] = useState(false);
  const [overviewSaveError, setOverviewSaveError] = useState<string | null>(null);

  // Step editing state for ai_thoughts inline edit
  const [editAiThoughts, setEditAiThoughts] = useState('');

  const overviews: Overview[] = data?.core_overview || [];

  // Best-effort: keep a local mapping for nicer provenance labels.
  // If assistant backend is unavailable, we still show raw IDs.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const threads = await assistantApi.getThreads();
        if (cancelled) return;
        const map: Record<string, string> = {};
        for (const t of threads) {
          if (t?.id != null) map[String(t.id)] = String(t.name || '').trim() || `Thread ${t.id}`;
        }
        setThreadNameById(map);
      } catch {
        // Non-fatal
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedStep = useMemo(() => {
    if (!selectedStepId) return null;
    for (const ov of overviews) {
      const steps = ov.core_steps || [];
      const found = steps.find((s) => s.id === selectedStepId);
      if (found) return found;
    }
    return null;
  }, [overviews, selectedStepId]);

  const selectedStepNoteContent = selectedStep?.core_stepnote?.content || '';

  // Get unique targets for filter dropdown
  const uniqueTargets = useMemo(() => {
    const targets = new Map<number, { id: number; name: string }>();
    overviews.forEach(ov => {
      if (!targets.has(ov.core_target!.id)) {
        targets.set(ov.core_target!.id, {
          id: ov.core_target!.id,
          name: ov.core_target!.name
        });
      }
    });
    return Array.from(targets.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [overviews]);

  // Filter and sort logic
  const filteredAndSortedOverviews = useMemo(() => {
    let filtered = [...overviews];

    // Filter by target
    if (selectedTargets.length > 0) {
      filtered = filtered.filter(ov => selectedTargets.includes(ov.core_target!.id));
    }

    // Filter by status
    if (selectedStatuses.length > 0) {
      filtered = filtered.filter(ov => selectedStatuses.includes(ov.status));
    }

    // Filter by search term
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(ov =>
        ov.core_target!.name.toLowerCase().includes(lowerSearch) ||
        ov.summary?.toLowerCase().includes(lowerSearch) ||
        ov.core_steps?.some(step =>
          (step.core_stepnote?.content || '').toLowerCase().includes(lowerSearch) ||
          step.core_attackvectors?.some(av => av.name.toLowerCase().includes(lowerSearch))
        )
      );
    }

    // Filter by time range
    if (timeRangeFilter !== 'all') {
      const cutoff = new Date();
      if (timeRangeFilter === '1h') cutoff.setHours(cutoff.getHours() - 1);
      else if (timeRangeFilter === '24h') cutoff.setDate(cutoff.getDate() - 1);
      else if (timeRangeFilter === '7d') cutoff.setDate(cutoff.getDate() - 7);

      filtered = filtered.filter(ov => new Date(ov.updated_at) >= cutoff);
    }

    // Sort
    if (sortBy === 'updated') {
      filtered.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    } else if (sortBy === 'created') {
      filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else if (sortBy === 'duration') {
      filtered.sort((a, b) => {
        const aDuration = new Date(a.updated_at).getTime() - new Date(a.created_at).getTime();
        const bDuration = new Date(b.updated_at).getTime() - new Date(b.created_at).getTime();
        return bDuration - aDuration;
      });
    } else if (sortBy === 'success_rate') {
      filtered.sort((a, b) => {
        const getSuccessRate = (steps: Step[] | undefined) => {
          if (!steps || steps.length === 0) return 0;
          const completed = steps.filter(s => s.status === 'COMPLETED').length;
          return completed / steps.length;
        };
        return getSuccessRate(b.core_steps) - getSuccessRate(a.core_steps);
      });
    }

    return filtered;
  }, [overviews, selectedTargets, selectedStatuses, searchTerm, timeRangeFilter, sortBy]);

  const toggleOverviewExpanded = useCallback((overviewId: number) => {
    const newExpanded = new Set(expandedOverviews);
    if (newExpanded.has(overviewId)) {
      newExpanded.delete(overviewId);
    } else {
      newExpanded.add(overviewId);
    }
    setExpandedOverviews(newExpanded);
  }, [expandedOverviews]);

  const handleTargetFilterChange = (targetId: number) => {
    const newSelected = new Set(selectedTargets);
    if (newSelected.has(targetId)) {
      newSelected.delete(targetId);
    } else {
      newSelected.add(targetId);
    }
    setSelectedTargets(Array.from(newSelected));
  };

  const handleStatusFilterChange = (status: string) => {
    const newSelected = new Set(selectedStatuses);
    if (newSelected.has(status)) {
      newSelected.delete(status);
    } else {
      newSelected.add(status);
    }
    setSelectedStatuses(Array.from(newSelected));
  };

  // Utility functions
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'COMPLETED':
      case 'SUCCESS':
        return '#10B981';
      case 'RUNNING':
        return '#fbbf24';
      case 'FAILED':
        return '#ef4444';
      case 'PLANNING':
      case 'PENDING':
        return '#6b7280';
      default:
        return '#94a3b8';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'COMPLETED':
        return '[OK]';
      case 'RUNNING':
        return '[>>]';
      case 'FAILED':
        return '[!!]';
      default:
        return '[..]';
    }
  };

  const formatDuration = (startDate: string, endDate: string | null | undefined): string => {
    if (!endDate) {
      // If not completed yet, show elapsed time from start
      const start = new Date(startDate).getTime();
      const now = new Date().getTime();
      const durationMs = now - start;
      
      if (durationMs < 1000) return `${durationMs}ms`;
      if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
      return `${(durationMs / 60000).toFixed(1)}m`;
    }
    
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const durationMs = end - start;
    
    if (durationMs < 1000) return `${durationMs}ms`;
    if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
    return `${(durationMs / 60000).toFixed(1)}m`;
  };

  const getStepSuccessRate = (steps: Step[] | undefined): number => {
    if (!steps || steps.length === 0) return 0;
    const completed = steps.filter(s => s.status === 'COMPLETED').length;
    return (completed / steps.length) * 100;
  };

  const getStepStats = (steps: Step[] | undefined) => {
    if (!steps || steps.length === 0) return { completed: 0, failed: 0, running: 0, pending: 0 };
    return {
      completed: steps.filter(s => s.status === 'COMPLETED').length,
      failed: steps.filter(s => s.status === 'FAILED').length,
      running: steps.filter(s => s.status === 'RUNNING').length,
      pending: steps.filter(s => !['COMPLETED', 'FAILED', 'RUNNING'].includes(s.status)).length,
    };
  };

  if (error) {
    return (
      <div className="execution-monitor-page">
        <div className="error-message">
          <span style={{ color: '#ef4444' }}>ERROR:</span> {error.message}
        </div>
      </div>
    );
  }

  return (
      <div style={{ display: 'flex', height: '100vh', gap: '0', overflow: 'hidden' }}>
        {/* Left: Execution Monitor */}
      <div
        className="execution-monitor-page"
        style={{
          flex: selectedStepId ? '1 1 60%' : '1 1 100%',
          transition: 'flex 0.3s ease',
          // Allow the left side to scroll while keeping the overall split view fixed.
          overflowY: 'auto',
          overflowX: 'hidden',
          minHeight: 0,
        }}
      >
        {/* Header */}
        <div className="exec-header">
          <h1 className="exec-title">EXECUTION MONITOR</h1>
          <div className="exec-status">
            {loading && <span style={{ color: '#fbbf24' }}>▢ LOADING...</span>}
            {!loading && <span style={{ color: '#10B981' }}>✓ LIVE</span>}
          </div>
        </div>

      {/* Controls Section */}
      <div className="exec-controls">
        {/* Search bar */}
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search by target name, step name, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        {/* Filter bars */}
        <div className="filter-section">
          {/* Time range filter */}
          <div className="filter-group">
            <label className="filter-label">TIME RANGE:</label>
            <div className="filter-buttons">
              {(['all', '1h', '24h', '7d'] as const).map(range => (
                <button
                  key={range}
                  className={`filter-btn ${timeRangeFilter === range ? 'active' : ''}`}
                  onClick={() => setTimeRangeFilter(range)}
                >
                  {range === 'all' ? 'All' : range}
                </button>
              ))}
            </div>
          </div>

          {/* Sort options */}
          <div className="filter-group">
            <label className="filter-label">SORT BY:</label>
            <div className="filter-buttons">
              {(['updated', 'created', 'duration', 'success_rate'] as const).map(option => (
                <button
                  key={option}
                  className={`filter-btn ${sortBy === option ? 'active' : ''}`}
                  onClick={() => setSortBy(option)}
                >
                  {option === 'updated' ? 'Updated' : option === 'created' ? 'Created' : option === 'duration' ? 'Duration' : 'Success Rate'}
                </button>
              ))}
            </div>
          </div>

          {/* Status filter */}
          <div className="filter-group">
            <label className="filter-label">STATUS:</label>
            <div className="filter-checkboxes">
              {['PLANNING', 'EXECUTING', 'COMPLETED', 'FAILED', 'STALLED'].map(status => (
                <label key={status} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes(status)}
                    onChange={() => handleStatusFilterChange(status)}
                  />
                  <span>{status}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Target filter */}
          {uniqueTargets.length > 0 && (
            <div className="filter-group">
              <label className="filter-label">TARGET:</label>
              <div className="filter-checkboxes">
                {uniqueTargets.map(target => (
                  <label key={target.id} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedTargets.includes(target.id)}
                      onChange={() => handleTargetFilterChange(target.id)}
                    />
                    <span>{target.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results summary */}
      <div className="results-summary">
        <span>{filteredAndSortedOverviews.length} Overviews</span>
        <span>•</span>
        <span>{filteredAndSortedOverviews.reduce((acc, ov) => acc + (ov.core_steps?.length || 0), 0)} Steps</span>
      </div>

      {/* Progress Tree View */}
      <div className="exec-tree-container">
        {filteredAndSortedOverviews.length === 0 ? (
          <div className="empty-state">
            <p>NO EXECUTION DATA FOUND</p>
            <p style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: '8px' }}>
              Try adjusting your filters or wait for agent activity to start.
            </p>
          </div>
        ) : (
          <div className="tree-nodes">
            {filteredAndSortedOverviews.map((overview) => {
              const isExpanded = expandedOverviews.has(overview.id);
              const steps = overview.core_steps || [];
              const stats = getStepStats(steps);
              const successRate = getStepSuccessRate(steps);
              const duration = formatDuration(overview.created_at, overview.updated_at);

              return (
                <div key={overview.id} className="tree-node overview-node">
                  {/* Overview Header (Collapsible) */}
                  <div className="node-header overview-header" onClick={() => toggleOverviewExpanded(overview.id)}>
                    <div className="node-expand-icon">{isExpanded ? '▼' : '▶'}</div>
                    
                    <div className="node-status-icon" style={{ color: getStatusColor(overview.status) }}>
                      {getStatusIcon(overview.status)}
                    </div>

                    <div className="node-content">
                      <div className="node-title">
                        <span className="target-name">{overview.core_target!.name}</span>
                        <span className="overview-id">#{overview.id}</span>
                      </div>
                      <div className="node-meta">
                        <span className="status-badge" style={{ color: getStatusColor(overview.status) }}>
                          {overview.status}
                        </span>
                        <span className="meta-divider">•</span>
                        <span className="risk-score">
                          Risk: <strong style={{ color: overview.risk_score >= 70 ? '#ef4444' : overview.risk_score >= 40 ? '#f59e0b' : '#10B981' }}>
                            {overview.risk_score}
                          </strong>
                        </span>
                        <span className="meta-divider">•</span>
                        <span className="duration">⏱ {duration}</span>
                        {(overview.thread_id || overview.parent_thread_id) && (
                          <>
                            <span className="meta-divider">•</span>
                            <span className="duration" style={{ opacity: 0.9 }}>
                              {(() => {
                                const originId = overview.parent_thread_id ?? overview.thread_id;
                                const originKey = originId != null ? String(originId) : null;
                                const originName = originKey ? threadNameById[originKey] : null;
                                return `origin:${originName ? ` ${originName}` : ''} (${originKey ?? '—'})`;
                              })()}
                            </span>
                            {(() => {
                              const originId = overview.parent_thread_id ?? overview.thread_id;
                              const originKey = originId != null ? String(originId) : null;
                              if (!originKey) return null;
                              return (
                                <button
                                  className="filter-btn"
                                  onClick={async (e) => {
                                    // Prevent collapsing/expanding overview when clicking this.
                                    e.stopPropagation();
                                    try {
                                      await navigator.clipboard.writeText(originKey);
                                    } catch {
                                      // ignore
                                    }
                                  }}
                                  title="Copy origin thread id"
                                >
                                  Copy thread
                                </button>
                              );
                            })()}
                          </>
                        )}
                      </div>
                    </div>

                    {/* Step Stats Bar */}
                    <div className="step-stats-bar">
                      <div className="stat-item">
                        <span className="stat-count" style={{ color: '#10B981' }}>{stats.completed}</span>
                        <span className="stat-label">OK</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-count" style={{ color: '#fbbf24' }}>{stats.running}</span>
                        <span className="stat-label">RUN</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-count" style={{ color: '#ef4444' }}>{stats.failed}</span>
                        <span className="stat-label">FAIL</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-count" style={{ color: '#6b7280' }}>{stats.pending}</span>
                        <span className="stat-label">WAIT</span>
                      </div>
                      {steps.length > 0 && (
                        <>
                          <span className="meta-divider">|</span>
                          <span className="success-rate" style={{ color: successRate >= 80 ? '#10B981' : successRate >= 50 ? '#f59e0b' : '#ef4444' }}>
                            {successRate.toFixed(0)}%
                          </span>
                        </>
                      )}
                      <span style={{ flex: 1 }} />
                      <button
                        className="filter-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingOverviewId(overview.id);
                          setEditOverviewFields({
                            status: overview.status,
                            summary: overview.summary || '',
                            risk_score: overview.risk_score,
                            business_impact: overview.business_impact || '',
                            plan: overview.plan ? (typeof overview.plan === 'string' ? overview.plan : JSON.stringify(overview.plan, null, 2)) : '',
                            knowledge: overview.knowledge ? (typeof overview.knowledge === 'string' ? overview.knowledge : JSON.stringify(overview.knowledge, null, 2)) : '',
                          });
                          setOverviewSaveError(null);
                        }}
                        title="Edit overview"
                        style={{ marginRight: 4 }}
                      >
                        Edit
                      </button>
                      <button
                        className="filter-btn"
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (!window.confirm(`Delete Overview #${overview.id} (${overview.core_target!.name})? All steps and logs will also be deleted.`)) return;
                          try {
                            await OverviewService.delete(overview.id);
                          } catch (err: any) {
                            alert('Delete failed: ' + (err?.message || 'unknown error'));
                          }
                        }}
                        title="Delete overview"
                        style={{ color: '#ef4444' }}
                      >
                        Del
                      </button>
                    </div>
                  </div>

                  {/* Expanded Step Tree */}
                  {isExpanded && (
                    <div className="node-children">
                      {steps.length === 0 ? (
                        <div className="no-steps">
                          <p>AWAITING_STEP_EXECUTION...</p>
                        </div>
                      ) : (
                        steps.map((step, stepIndex) => {
                          // Prefer human-facing StepNote as the step display label.
                          const stepName =
                            step.core_stepnote?.content ||
                            step.core_attackvectors?.[0]?.name ||
                            `Step #${step.id}`;
                          const stepDuration = formatDuration(step.created_at, step.completed_at);
                          const isLastStep = stepIndex === steps.length - 1;
                          // Interval since previous step
                          const prevStep = stepIndex > 0 ? steps[stepIndex - 1] : null;
                          const stepInterval = prevStep
                            ? formatDuration(prevStep.completed_at || prevStep.created_at, step.created_at)
                            : null;

                          return (
                            <div 
                              key={step.id} 
                              className={`tree-node step-node ${selectedStepId === step.id ? 'selected' : ''}`}
                              onClick={() => setSelectedStepId(step.id)}
                              style={{ cursor: 'pointer' }}
                            >
                              {/* Vertical connector line */}
                              {!isLastStep && <div className="tree-connector" />}

                              <div className="node-header step-header">
                                <div className="tree-branch-icon">├</div>
                                
                                <div className="node-status-icon" style={{ color: getStatusColor(step.status) }}>
                                  {getStatusIcon(step.status)}
                                </div>

                                <div className="node-content">
                                  <div className="node-title">
                                    <span className="step-name">{stepName}</span>
                                  </div>
                                  <div className="node-meta">
                                    <span className="status-badge" style={{ color: getStatusColor(step.status) }}>
                                      {step.status}
                                    </span>
                                    <span className="meta-divider">•</span>
                                    <span className="duration">⏱ {stepDuration}</span>
                                    {stepInterval && (
                                      <>
                                        <span className="meta-divider">•</span>
                                        <span className="duration" style={{ opacity: 0.6 }}>↳{stepInterval}</span>
                                      </>
                                    )}
                                    {step.core_stepnote?.ai_thoughts && (
                                      <>
                                        <span className="meta-divider">•</span>
                                        <span className="has-ai-thoughts">💭 Has AI insights</span>
                                      </>
                                    )}
                                    <span style={{ flex: 1 }} />
                                    <button
                                      className="filter-btn"
                                      onClick={async (e) => {
                                        e.stopPropagation();
                                        if (!window.confirm(`Delete Step #${step.id}?`)) return;
                                        try {
                                          await StepService.delete(step.id);
                                          if (selectedStepId === step.id) setSelectedStepId(null);
                                        } catch (err: any) {
                                          alert('Delete failed: ' + (err?.message || 'unknown'));
                                        }
                                      }}
                                      title="Delete step"
                                      style={{ color: '#ef4444', fontSize: 11, padding: '1px 6px' }}
                                    >
                                      Del
                                    </button>
                                  </div>

                                  {/* Attack vectors info */}
                                  {step.core_attackvectors && step.core_attackvectors.length > 0 && (
                                    <div className="attack-vectors">
                                      {step.core_attackvectors.map(av => (
                                        <div key={av.id} className="attack-vector-tag">
                                          {av.vector_type && <span className="av-type">[{av.vector_type}]</span>}
                                          <span className="av-name">{av.name}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}

                                  {/* StepNote preview: first line only (human-facing summary). Full details in right panel. */}
                                  <div className="step-note-preview">
                                    {step.core_stepnote?.content
                                      ? (
                                          <>
                                            {(step.core_stepnote.content.split('\n')[0] || '').substring(0, 150)}
                                            {(step.core_stepnote.content.split('\n')[0] || '').length > 150 ? '...' : ''}
                                          </>
                                        )
                                      : (
                                          <span style={{ opacity: 0.75, fontStyle: 'italic' }}>
                                            No StepNote yet
                                          </span>
                                        )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              );
            })}
           </div>
         )}
        </div>
      </div>

      {/* Overview Edit Modal */}
      {editingOverviewId !== null && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', zIndex: 9999,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          onClick={() => setEditingOverviewId(null)}
        >
          <div
            style={{
              background: '#fff', borderRadius: 12, padding: 24, width: 800,
              maxWidth: '92vw', maxHeight: '85vh', overflowY: 'auto',
              boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 700 }}>
              Overview #{editingOverviewId}
            </h3>

            {/* Read-only info bar */}
            {(() => {
              const ov = overviews.find(o => o.id === editingOverviewId);
              if (!ov) return null;
              return (
                <div style={{
                  background: '#f3f4f6', borderRadius: 8, padding: '10px 14px',
                  marginBottom: 16, fontSize: 12, display: 'flex', flexWrap: 'wrap', gap: '12px',
                }}>
                  <span><strong>Target:</strong> {ov.core_target?.name || '—'}</span>
                  <span><strong>Created:</strong> {new Date(ov.created_at).toLocaleString()}</span>
                  <span><strong>Updated:</strong> {new Date(ov.updated_at).toLocaleString()}</span>
                  <span><strong>Thread:</strong> {ov.thread_id ?? '—'}</span>
                  <span><strong>Parent Thread:</strong> {ov.parent_thread_id ?? '—'}</span>
                </div>
              );
            })()}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
                Status
                <select
                  value={editOverviewFields.status}
                  onChange={(e) => setEditOverviewFields(p => ({ ...p, status: e.target.value }))}
                  style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                >
                  {['PLANNING', 'EXECUTING', 'STALLED', 'COMPLETED'].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </label>

              <div style={{ display: 'flex', gap: 12 }}>
                <label style={{ flex: 1, fontSize: 12, fontWeight: 600, color: '#374151' }}>
                  Risk Score (0-100)
                  <input
                    type="number" min={0} max={100}
                    value={editOverviewFields.risk_score}
                    onChange={(e) => setEditOverviewFields(p => ({ ...p, risk_score: Math.min(100, Math.max(0, Number(e.target.value)) || 0) }))}
                    style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                  />
                </label>
                <label style={{ flex: 1, fontSize: 12, fontWeight: 600, color: '#374151' }}>
                  Business Impact
                  <select
                    value={editOverviewFields.business_impact}
                    onChange={(e) => setEditOverviewFields(p => ({ ...p, business_impact: e.target.value }))}
                    style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                  >
                    <option value="">—</option>
                    {['Critical', 'High', 'Medium', 'Low'].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
                Summary
                <textarea
                  rows={4}
                  value={editOverviewFields.summary}
                  onChange={(e) => setEditOverviewFields(p => ({ ...p, summary: e.target.value }))}
                  style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13, resize: 'vertical', fontFamily: 'monospace' }}
                />
              </label>

              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
                Plan (JSON)
                <textarea
                  rows={6}
                  value={editOverviewFields.plan}
                  onChange={(e) => setEditOverviewFields(p => ({ ...p, plan: e.target.value }))}
                  style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 12, resize: 'vertical', fontFamily: 'monospace' }}
                  placeholder='{"steps": [...]}'
                />
              </label>

              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
                Knowledge (JSON)
                <textarea
                  rows={6}
                  value={editOverviewFields.knowledge}
                  onChange={(e) => setEditOverviewFields(p => ({ ...p, knowledge: e.target.value }))}
                  style={{ width: '100%', marginTop: 4, padding: '6px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 12, resize: 'vertical', fontFamily: 'monospace' }}
                />
              </label>
            </div>

            {overviewSaveError && (
              <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{overviewSaveError}</div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button
                className="filter-btn"
                onClick={() => setEditingOverviewId(null)}
                disabled={isSavingOverview}
              >
                Cancel
              </button>
              <button
                className="filter-btn active"
                disabled={isSavingOverview}
                onClick={async () => {
                  setIsSavingOverview(true);
                  setOverviewSaveError(null);
                  try {
                    const payload: any = {
                      status: editOverviewFields.status,
                      summary: editOverviewFields.summary || null,
                      risk_score: editOverviewFields.risk_score,
                      business_impact: editOverviewFields.business_impact || null,
                    };
                    // Try to parse plan/knowledge as JSON; fallback to raw string
                    if (editOverviewFields.plan) {
                      try { payload.plan = JSON.parse(editOverviewFields.plan); }
                      catch { payload.plan = editOverviewFields.plan; }
                    }
                    if (editOverviewFields.knowledge) {
                      try { payload.knowledge = JSON.parse(editOverviewFields.knowledge); }
                      catch { payload.knowledge = editOverviewFields.knowledge; }
                    }
                    await OverviewService.update(editingOverviewId, payload);
                    setEditingOverviewId(null);
                  } catch (err: any) {
                    setOverviewSaveError(String(err?.response?.data?.detail || err?.message || 'Save failed'));
                  } finally {
                    setIsSavingOverview(false);
                  }
                }}
              >
                {isSavingOverview ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Right: Step Log Viewer */}
      {selectedStepId && (
        <div
          style={{
            flex: '1 1 40%',
            borderLeft: '2px solid #e5e7eb',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: '12px 16px',
              background: '#f3f4f6',
              borderBottom: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontWeight: 600, fontSize: '13px' }}>
              Step #{selectedStepId} Logs
            </span>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              {/* Retry: reset FAILED step to PENDING */}
              {selectedStep?.status === 'FAILED' && (
                <button
                  className="filter-btn"
                  onClick={async () => {
                    try {
                      await StepService.update(selectedStepId, { status: 'PENDING' });
                    } catch (err: any) {
                      alert('Retry failed: ' + (err?.message || 'unknown'));
                    }
                  }}
                  title="Reset to PENDING for retry"
                  style={{ color: '#f59e0b' }}
                >
                  Retry
                </button>
              )}
              {/* Delete this step */}
              <button
                className="filter-btn"
                onClick={async () => {
                  if (!window.confirm(`Delete Step #${selectedStepId}?`)) return;
                  try {
                    await StepService.delete(selectedStepId);
                    setSelectedStepId(null);
                  } catch (err: any) {
                    alert('Delete failed: ' + (err?.message || 'unknown'));
                  }
                }}
                title="Delete step"
                style={{ color: '#ef4444' }}
              >
                Del
              </button>
              <button
                onClick={() => setSelectedStepId(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px',
                  color: '#9ca3af',
                }}
              >
                ✕
              </button>
            </div>
          </div>
          {/* StepNote (human-facing) */}
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid #e5e7eb',
              background: '#ffffff',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
              <div style={{ fontWeight: 700, fontSize: '12px', letterSpacing: '0.04em', textTransform: 'uppercase', color: '#374151' }}>
                StepNote (Summary)
              </div>
              <button
                className="filter-btn"
                onClick={() => {
                  setIsEditingNote((v) => {
                    const next = !v;
                    if (!v && next) {
                      setEditNoteContent(selectedStepNoteContent);
                      setEditAiThoughts(selectedStep?.core_stepnote?.ai_thoughts || '');
                      setNoteSaveError(null);
                    }
                    return next;
                  });
                }}
              >
                {isEditingNote ? 'Close' : 'Edit'}
              </button>
            </div>

            {isEditingNote ? (
              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: 11, fontWeight: 600, color: '#374151' }}>Summary (human-facing)</label>
                <textarea
                  value={editNoteContent}
                  onChange={(e) => setEditNoteContent(e.target.value)}
                  rows={6}
                  style={{
                    width: '100%',
                    resize: 'vertical',
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    color: '#111827',
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                    fontSize: '12px',
                  }}
                />
                <label style={{ fontSize: 11, fontWeight: 600, color: '#374151', marginTop: 4 }}>
                  Reason / AI Thoughts (why this step exists)
                </label>
                <textarea
                  value={editAiThoughts}
                  onChange={(e) => setEditAiThoughts(e.target.value)}
                  rows={4}
                  style={{
                    width: '100%',
                    resize: 'vertical',
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    color: '#111827',
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                    fontSize: '12px',
                  }}
                  placeholder="AI's reasoning for creating this step — what it was trying to achieve"
                />
                {noteSaveError && (
                  <div style={{ color: '#ef4444', fontSize: '12px' }}>{noteSaveError}</div>
                )}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <button
                    className="filter-btn"
                    onClick={() => {
                      setIsEditingNote(false);
                      setEditNoteContent('');
                      setEditAiThoughts('');
                      setNoteSaveError(null);
                    }}
                    disabled={isSavingNote}
                  >
                    Cancel
                  </button>
                  <button
                    className="filter-btn active"
                    onClick={async () => {
                      setIsSavingNote(true);
                      setNoteSaveError(null);
                      try {
                        await StepService.upsertNote(selectedStepId, {
                          content: editNoteContent,
                          ai_thoughts: editAiThoughts || null,
                        });
                        setIsEditingNote(false);
                      } catch (err: any) {
                        const msg = err?.response?.data?.detail || err?.message || 'Save failed';
                        setNoteSaveError(String(msg));
                      } finally {
                        setIsSavingNote(false);
                      }
                    }}
                    disabled={isSavingNote}
                  >
                    {isSavingNote ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ marginTop: '10px', fontSize: '12px', color: '#111827', whiteSpace: 'pre-wrap' }}>
                {selectedStepNoteContent ? selectedStepNoteContent.split('\n')[0] : 'No StepNote yet'}
              </div>
            )}

            {/* Step reason: StepNote.ai_thoughts (operator-facing) */}
            {!isEditingNote && selectedStep?.core_stepnote?.ai_thoughts && (
              <details style={{ marginTop: 10 }}>
                <summary style={{ cursor: 'pointer', fontSize: '12px', color: '#374151', fontWeight: 600 }}>
                  Reason (AI Thoughts)
                </summary>
                <div style={{ marginTop: 8, fontSize: '12px', color: '#111827', whiteSpace: 'pre-wrap' }}>
                  {selectedStep.core_stepnote.ai_thoughts}
                </div>
              </details>
            )}
          </div>

          {/* StepLogViewer (full execution trace) */}
          <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
            <StepLogViewer stepId={selectedStepId} autoScroll={true} />
          </div>
        </div>
      )}
    </div>
   );
 }
