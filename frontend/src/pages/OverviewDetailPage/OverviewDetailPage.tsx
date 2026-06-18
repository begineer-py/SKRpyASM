import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useHasuraQuery } from '../../hooks/useHasuraQuery';
import { GET_SINGLE_OVERVIEW } from '../../queries';
import { OverviewService } from '../../services/overviewService';
import type { OverviewUpdatePayload } from '../../services/overviewService';
import { executionApi } from '../../services/executionApi';
import './OverviewDetail.css';

interface OverviewData {
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
  thread_id?: number;
  parent_thread_id?: number;
  core_target: {
    id: number;
    name: string;
    description?: string;
  };
}

const OverviewDetailPage: React.FC = () => {
  const { overviewId } = useParams<{ overviewId: string }>();
  const navigate = useNavigate();
  const id = parseInt(overviewId || '0');

  const { data, loading, error, refetch } = useHasuraQuery(GET_SINGLE_OVERVIEW, { id });

  const [editFields, setEditFields] = useState<OverviewUpdatePayload>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'plan' | 'knowledge' | 'techs' | 'executions'>('summary');

  const overview: OverviewData | null = data?.core_overview_by_pk;

  useEffect(() => {
    if (overview) {
      setEditFields({
        summary: overview.summary || '',
        status: overview.status,
        risk_score: overview.risk_score,
        business_impact: overview.business_impact || '',
        plan: overview.plan,
        knowledge: overview.knowledge,
      });
    }
  }, [overview]);

  if (loading) return <div className="overview-detail-loading">LOADING_OVERVIEW_DATA...</div>;
  if (error) return <div className="overview-detail-error">ERROR: {error.message}</div>;
  if (!overview) return <div className="overview-detail-error">OVERVIEW_NOT_FOUND (ID: {id})</div>;

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      // Ensure JSON fields are parsed if edited as strings
      const payload: OverviewUpdatePayload = { ...editFields };
      if (typeof payload.plan === 'string') {
        try { payload.plan = JSON.parse(payload.plan); } catch (e) { throw new Error('Invalid JSON in Plan'); }
      }
      if (typeof payload.knowledge === 'string') {
        try { payload.knowledge = JSON.parse(payload.knowledge); } catch (e) { throw new Error('Invalid JSON in Knowledge'); }
      }

      await OverviewService.update(id, payload);
      refetch();
      alert('Overview updated successfully');
    } catch (err: any) {
      setSaveError(err.message || 'Failed to update overview');
    } finally {
      setIsSaving(false);
    }
  };

  const renderJsonEditor = (field: keyof OverviewUpdatePayload) => {
    const val = editFields[field];
    const displayVal = typeof val === 'string' ? val : JSON.stringify(val, null, 2);
    return (
      <textarea
        className="overview-json-editor"
        value={displayVal}
        onChange={(e) => setEditFields({ ...editFields, [field]: e.target.value })}
        spellCheck={false}
      />
    );
  };

  return (
    <div className="c2-page overview-detail-page">
      <div className="overview-detail-header">
        <div className="header-left">
          <button className="back-btn" onClick={() => navigate(-1)}>← BACK</button>
          <h1 className="overview-title">
            OVERVIEW <span className="id-highlight">#{overview.id}</span>
            <span className="target-name-sub">@{overview.core_target.name}</span>
          </h1>
        </div>
        <div className="header-actions">
          {saveError && <span className="save-error">{saveError}</span>}
          <button 
            className="save-btn" 
            onClick={handleSave} 
            disabled={isSaving}
          >
            {isSaving ? 'SAVING...' : 'SAVE_CHANGES'}
          </button>
        </div>
      </div>

      <div className="overview-grid">
        {/* Left Column: Metadata */}
        <div className="overview-meta-card">
          <div className="meta-section">
            <label>STATUS</label>
            <select 
              value={editFields.status || ''} 
              onChange={(e) => setEditFields({ ...editFields, status: e.target.value })}
            >
              <option value="PLANNING">PLANNING</option>
              <option value="EXECUTING">EXECUTING</option>
              <option value="STALLED">STALLED</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="NEEDS_GUIDANCE">NEEDS_GUIDANCE</option>
            </select>
          </div>

          <div className="meta-section">
            <label>RISK_SCORE (0-100)</label>
            <input 
              type="number" 
              min="0" max="100"
              value={editFields.risk_score || 0}
              onChange={(e) => setEditFields({ ...editFields, risk_score: parseInt(e.target.value) })}
            />
          </div>

          <div className="meta-section">
            <label>BUSINESS_IMPACT</label>
            <select 
              value={editFields.business_impact || ''} 
              onChange={(e) => setEditFields({ ...editFields, business_impact: e.target.value })}
            >
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="">N/A</option>
            </select>
          </div>

          <div className="meta-info-footer">
            <div className="info-row">
              <span>CREATED:</span>
              <span>{new Date(overview.created_at).toLocaleString()}</span>
            </div>
            <div className="info-row">
              <span>UPDATED:</span>
              <span>{new Date(overview.updated_at).toLocaleString()}</span>
            </div>
            <div className="info-row">
              <span>THREAD_ID:</span>
              <code>{overview.thread_id || 'NONE'}</code>
            </div>
            <div className="info-row">
              <span>PARENT_THREAD:</span>
              <code>{overview.parent_thread_id || 'NONE'}</code>
            </div>
            {overview.thread_id && (
              <button
                className="c2-btn c2-btn--ghost"
                style={{ marginTop: 8, fontSize: '0.75rem', width: '100%' }}
                onClick={() => navigate(`/aicenter?thread=${overview.thread_id}`)}
              >
                OPEN IN AI CENTER ↗
              </button>
            )}
          </div>
        </div>

        {/* Right Column: Content Tabs */}
        <div className="overview-content-card">
          <div className="content-tabs">
            <button 
              className={activeTab === 'summary' ? 'active' : ''} 
              onClick={() => setActiveTab('summary')}
            >
              SUMMARY
            </button>
            <button 
              className={activeTab === 'plan' ? 'active' : ''} 
              onClick={() => setActiveTab('plan')}
            >
              ATTACK_PLAN
            </button>
            <button 
              className={activeTab === 'knowledge' ? 'active' : ''} 
              onClick={() => setActiveTab('knowledge')}
            >
              KNOWLEDGE_BASE
            </button>
            <button
              className={activeTab === 'techs' ? 'active' : ''}
              onClick={() => setActiveTab('techs')}
            >
              TECH_STACK
            </button>
            <button
              className={activeTab === 'executions' ? 'active' : ''}
              onClick={() => setActiveTab('executions')}
            >
              EXECUTIONS
            </button>
          </div>

          <div className="tab-body">
            {activeTab === 'summary' && (
              <textarea
                className="overview-summary-editor"
                value={editFields.summary || ''}
                onChange={(e) => setEditFields({ ...editFields, summary: e.target.value })}
                placeholder="Write target summary/notes here..."
              />
            )}
            {activeTab === 'plan' && renderJsonEditor('plan')}
            {activeTab === 'knowledge' && renderJsonEditor('knowledge')}
            {activeTab === 'techs' && (
              <div className="tech-stack-viewer">
                <pre><code>{JSON.stringify(overview.techs, null, 2)}</code></pre>
                <p className="hint">Tech stack is currently read-only (managed by sensors).</p>
              </div>
            )}
            {activeTab === 'executions' && overview.thread_id && (
              <OverviewExecutions threadId={overview.thread_id} />
            )}
            {activeTab === 'executions' && !overview.thread_id && (
              <div style={{ color: '#64748b', padding: 16 }}>No thread linked to this overview.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewDetailPage;

function OverviewExecutions({ threadId }: { threadId: number }) {
  const [graphs, setGraphs] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    executionApi.listGraphs({ thread_id: threadId, limit: 20 }).then(setGraphs).catch(() => setGraphs([]));
  }, [threadId]);

  if (graphs.length === 0) return <div style={{ color: '#64748b', padding: 16 }}>No execution graphs found.</div>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {graphs.map(g => (
        <div
          key={g.id}
          style={{ padding: 12, background: 'rgba(15,23,42,0.7)', borderRadius: 8, border: '1px solid rgba(148,163,184,0.18)', cursor: 'pointer' }}
          onClick={() => navigate(`/execution-monitor?graph=${g.id}`)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <strong>Graph #{g.id}</strong>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>{g.status}</span>
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            {g.assistant_id} · {new Date(g.started_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
