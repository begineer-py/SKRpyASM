import { useState, useMemo, useCallback } from 'react';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { GET_ALL_EXECUTION_STEPS } from '../../queries';
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
  plan?: string;
  knowledge?: string;
  created_at: string;
  updated_at: string;
  core_target: {
    id: number;
    name: string;
    description?: string;
  };
  core_steps?: Step[];
}

export default function ExecutionMonitorPage() {
  const { data, loading, error } = useHasuraSubscription(GET_ALL_EXECUTION_STEPS);
  
  // Filter states
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [timeRangeFilter, setTimeRangeFilter] = useState<'all' | '1h' | '24h' | '7d'>('all');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'duration' | 'success_rate'>('updated');
  
  // State for expanded overview items
  const [expandedOverviews, setExpandedOverviews] = useState<Set<number>>(new Set());

  const overviews: Overview[] = data?.core_overview || [];

  // Get unique targets for filter dropdown
  const uniqueTargets = useMemo(() => {
    const targets = new Map<number, { id: number; name: string }>();
    overviews.forEach(ov => {
      if (!targets.has(ov.core_target.id)) {
        targets.set(ov.core_target.id, {
          id: ov.core_target.id,
          name: ov.core_target.name
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
      filtered = filtered.filter(ov => selectedTargets.includes(ov.core_target.id));
    }

    // Filter by status
    if (selectedStatuses.length > 0) {
      filtered = filtered.filter(ov => selectedStatuses.includes(ov.status));
    }

    // Filter by search term
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(ov =>
        ov.core_target.name.toLowerCase().includes(lowerSearch) ||
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
    <div className="execution-monitor-page">
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
                        <span className="target-name">{overview.core_target.name}</span>
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
                          const stepName = 
                            step.core_attackvectors?.[0]?.name ||
                            step.core_stepnote?.content ||
                            `Step #${step.id}`;
                          const stepDuration = formatDuration(step.created_at, step.completed_at);
                          const isLastStep = stepIndex === steps.length - 1;

                          return (
                            <div key={step.id} className="tree-node step-node">
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
                                    {step.core_stepnote?.ai_thoughts && (
                                      <>
                                        <span className="meta-divider">•</span>
                                        <span className="has-ai-thoughts">💭 Has AI insights</span>
                                      </>
                                    )}
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

                                  {/* Step note preview */}
                                  {step.core_stepnote?.content && (
                                    <div className="step-note-preview">
                                      {step.core_stepnote.content.substring(0, 150)}
                                      {step.core_stepnote.content.length > 150 ? '...' : ''}
                                    </div>
                                  )}
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
  );
}
