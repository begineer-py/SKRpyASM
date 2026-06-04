import { useState, useEffect } from 'react';
import { GLOBAL_CONFIG } from '../../config';
import './AgentLLMConfig.css';

interface APIKeyBrief {
  id: number;
  service_name: string;
  description: string | null;
}

interface AgentLLMConfigDB {
  id: number;
  agent_id: string;
  provider: string | null;
  model_name: string | null;
  temperature: number | null;
  api_base_url: string | null;
  api_key_ref: APIKeyBrief | null;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

interface AgentEffectiveConfig {
  agent_id: string;
  effective_provider: string;
  effective_model: string;
  effective_temperature: number;
  effective_api_base_url: string | null;
  has_db_config: boolean;
  has_env_override: boolean;
  db_config: AgentLLMConfigDB | null;
}

interface APIKey {
  id: number;
  service_name: string;
  key_value: string;
  is_active: boolean;
  description: string | null;
}

interface EditForm {
  provider: string;
  model_name: string;
  temperature: string;
  api_base_url: string;
  api_key_id: string;
  description: string;
}

const PROVIDERS = ['openai', 'anthropic', 'mistral', 'deepseek', 'ollama'];
const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

const NO_KEY_VALUE = '__none__';

function StatusBadge({ config }: { config: AgentEffectiveConfig }) {
  if (config.has_db_config) {
    return <span className="agent-status-badge db-override">DB OVERRIDE</span>;
  }
  if (config.has_env_override) {
    return <span className="agent-status-badge env-var">ENV VAR</span>;
  }
  return <span className="agent-status-badge default">DEFAULT</span>;
}

const AgentLLMConfigPage: React.FC = () => {
  const [configs, setConfigs] = useState<AgentEffectiveConfig[]>([]);
  const [allKeys, setAllKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    provider: '',
    model_name: '',
    temperature: '0',
    api_base_url: '',
    api_key_id: NO_KEY_VALUE,
    description: '',
  });
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfgRes, keysRes] = await Promise.all([
        fetch(`${apiBase}/api_keys/agent-configs/`),
        fetch(`${apiBase}/api_keys/`),
      ]);
      if (!cfgRes.ok) throw new Error('Failed to fetch agent configs');
      if (!keysRes.ok) throw new Error('Failed to fetch API keys');
      const [cfgData, keysData] = await Promise.all([cfgRes.json(), keysRes.json()]);
      setConfigs(Array.isArray(cfgData) ? cfgData : []);
      setAllKeys(Array.isArray(keysData) ? keysData : []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openEdit = (cfg: AgentEffectiveConfig) => {
    const db = cfg.db_config;
    setEditForm({
      provider: db?.provider ?? cfg.effective_provider ?? '',
      model_name: db?.model_name ?? cfg.effective_model ?? '',
      temperature: String(db?.temperature ?? cfg.effective_temperature ?? 0),
      api_base_url: db?.api_base_url ?? cfg.effective_api_base_url ?? '',
      api_key_id: db?.api_key_ref ? String(db.api_key_ref.id) : NO_KEY_VALUE,
      description: db?.description ?? '',
    });
    setEditingAgentId(cfg.agent_id);
  };

  const handleSave = async () => {
    if (!editingAgentId) return;
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        provider: editForm.provider || null,
        model_name: editForm.model_name || null,
        temperature: editForm.temperature !== '' ? parseFloat(editForm.temperature) : null,
        api_base_url: editForm.api_base_url || null,
        api_key_id: editForm.api_key_id !== NO_KEY_VALUE ? parseInt(editForm.api_key_id, 10) : null,
        description: editForm.description || null,
      };
      const res = await fetch(`${apiBase}/api_keys/agent-configs/${editingAgentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Save failed');
      setEditingAgentId(null);
      await fetchData();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async (agentId: string) => {
    if (!confirm(`Reset "${agentId}" to env var / global default?`)) return;
    try {
      const res = await fetch(`${apiBase}/api_keys/agent-configs/${agentId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Reset failed');
      await fetchData();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  // Keys filtered by selected provider for the dropdown
  const relevantKeys = editForm.provider
    ? allKeys.filter(k => k.service_name.toLowerCase() === editForm.provider.toLowerCase() && k.is_active)
    : allKeys.filter(k => k.is_active);

  return (
    <div className="c2-page agent-config-container">
      <div className="agent-config-header">
        <div className="agent-config-header-left">
          <h1 className="agent-config-title">
            <span className="agent-bracket">[</span>
            AGENT_LLM_CONFIG
            <span className="agent-bracket">]</span>
          </h1>
          <span className="agent-config-subtitle">
            Agent 獨立模型配置 — DB 覆蓋 / Env Var / 全域默認
          </span>
        </div>
        <button className="btn btn-secondary" onClick={fetchData} disabled={loading}>
          {loading ? '...' : '↺ REFRESH'}
        </button>
      </div>

      {/* Priority Legend */}
      <div className="agent-priority-bar">
        <span className="priority-label">PRIORITY:</span>
        <span className="agent-status-badge db-override">DB OVERRIDE</span>
        <span className="priority-arrow">&gt;</span>
        <span className="agent-status-badge env-var">ENV VAR</span>
        <span className="priority-arrow">&gt;</span>
        <span className="agent-status-badge default">DEFAULT</span>
      </div>

      {loading && <div className="agent-loading">LOADING AGENT CONFIGS...</div>}
      {error && <div className="agent-error">⚠ {error}</div>}

      {!loading && !error && (
        <div className="agent-list">
          {configs.map(cfg => (
            <div key={cfg.agent_id} className={`agent-card ${cfg.has_db_config ? 'has-db' : ''}`}>
              <div className="agent-card-header">
                <div className="agent-id-row">
                  <span className="agent-id">{cfg.agent_id}</span>
                  <StatusBadge config={cfg} />
                </div>
                <div className="agent-card-actions">
                  <button className="btn btn-secondary btn-sm" onClick={() => openEdit(cfg)}>
                    EDIT
                  </button>
                  {cfg.has_db_config && (
                    <button className="btn btn-danger btn-sm" onClick={() => handleReset(cfg.agent_id)}>
                      RESET
                    </button>
                  )}
                </div>
              </div>

              <div className="agent-card-body">
                <div className="agent-info-grid">
                  <div className="agent-info-item">
                    <span className="info-label">PROVIDER</span>
                    <span className="info-value provider-value">{cfg.effective_provider}</span>
                  </div>
                  <div className="agent-info-item">
                    <span className="info-label">MODEL</span>
                    <span className="info-value model-value">{cfg.effective_model}</span>
                  </div>
                  <div className="agent-info-item">
                    <span className="info-label">TEMP</span>
                    <span className="info-value">{cfg.effective_temperature.toFixed(1)}</span>
                  </div>
                  <div className="agent-info-item">
                    <span className="info-label">API KEY</span>
                    <span className="info-value key-ref-value">
                      {cfg.db_config?.api_key_ref
                        ? `${cfg.db_config.api_key_ref.service_name} (••••${cfg.db_config.api_key_ref.id})`
                        : '— global fallback —'}
                    </span>
                  </div>
                  {cfg.effective_api_base_url && (
                    <div className="agent-info-item full-width">
                      <span className="info-label">BASE URL</span>
                      <span className="info-value url-value">{cfg.effective_api_base_url}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingAgentId && (
        <div className="modal-overlay" onClick={() => setEditingAgentId(null)}>
          <div className="modal agent-modal" onClick={e => e.stopPropagation()}>
            <h3>EDIT: {editingAgentId}</h3>

            <label className="modal-label">PROVIDER</label>
            <select
              value={editForm.provider}
              onChange={e => setEditForm({ ...editForm, provider: e.target.value })}
            >
              <option value="">— inherit global default —</option>
              {PROVIDERS.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>

            <label className="modal-label">MODEL NAME</label>
            <input
              type="text"
              placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022"
              value={editForm.model_name}
              onChange={e => setEditForm({ ...editForm, model_name: e.target.value })}
            />

            <label className="modal-label">TEMPERATURE (0.0 – 2.0)</label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={editForm.temperature}
              onChange={e => setEditForm({ ...editForm, temperature: e.target.value })}
            />

            <label className="modal-label">API BASE URL (optional)</label>
            <input
              type="text"
              placeholder="https://api.openai.com/v1"
              value={editForm.api_base_url}
              onChange={e => setEditForm({ ...editForm, api_base_url: e.target.value })}
            />

            <label className="modal-label">
              API KEY REFERENCE {editForm.provider ? `(${editForm.provider} keys)` : '(all active keys)'}
            </label>
            <select
              value={editForm.api_key_id}
              onChange={e => setEditForm({ ...editForm, api_key_id: e.target.value })}
            >
              <option value={NO_KEY_VALUE}>— Use Global Provider Key —</option>
              {relevantKeys.map(k => (
                <option key={k.id} value={String(k.id)}>
                  [{k.service_name}] ••••{k.key_value.slice(-4)}
                  {k.description ? ` — ${k.description}` : ''}
                </option>
              ))}
            </select>

            <label className="modal-label">DESCRIPTION (optional)</label>
            <input
              type="text"
              placeholder="e.g. Uses GPT-4o for complex exploit analysis"
              value={editForm.description}
              onChange={e => setEditForm({ ...editForm, description: e.target.value })}
            />

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setEditingAgentId(null)}>
                CANCEL
              </button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? 'SAVING...' : 'SAVE CONFIG'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentLLMConfigPage;
