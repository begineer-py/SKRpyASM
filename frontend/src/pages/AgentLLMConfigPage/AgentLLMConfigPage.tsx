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

interface TestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
  model_used: string | null;
  provider_used: string;
}

interface EditForm {
  provider: string;          // KNOWN_PROVIDERS value or CUSTOM_PROVIDER sentinel
  custom_provider: string;   // actual value when provider === CUSTOM_PROVIDER
  model_name: string;
  temperature: string;
  api_base_url: string;
  api_key_id: string;
  description: string;
}

const KNOWN_PROVIDERS = ['openai', 'anthropic', 'mistral', 'deepseek', 'ollama'];
const CUSTOM_PROVIDER = '__custom__';
const NO_KEY_VALUE = '__none__';
const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

function StatusBadge({ config }: { config: AgentEffectiveConfig }) {
  if (config.has_db_config) {
    return <span className="agent-status-badge db-override">DB OVERRIDE</span>;
  }
  if (config.has_env_override) {
    return <span className="agent-status-badge env-var">ENV VAR</span>;
  }
  return <span className="agent-status-badge default">DEFAULT</span>;
}

function TestResultDisplay({ result }: { result: TestResult }) {
  const cls = result.success ? 'success' : 'failure';
  const icon = result.success ? '✓' : '✗';
  const latency = result.latency_ms != null ? ` — ${result.latency_ms}ms` : '';
  const msg = result.message.length > 120 ? result.message.slice(0, 120) + '…' : result.message;
  return (
    <div className={`test-result ${cls}`}>
      {icon} {msg}{latency}
    </div>
  );
}

const AgentLLMConfigPage: React.FC = () => {
  const [configs, setConfigs] = useState<AgentEffectiveConfig[]>([]);
  const [allKeys, setAllKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    provider: '',
    custom_provider: '',
    model_name: '',
    temperature: '0',
    api_base_url: '',
    api_key_id: NO_KEY_VALUE,
    description: '',
  });
  const [saving, setSaving] = useState(false);

  // Per-modal test state
  const [modalTesting, setModalTesting] = useState(false);
  const [modalTestResult, setModalTestResult] = useState<TestResult | null>(null);

  // Per-card inline test state
  const [cardTestState, setCardTestState] = useState<Record<string, { loading: boolean; result: TestResult | null }>>({});

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

  useEffect(() => { fetchData(); }, []);

  // Derive actual provider value from form state
  const getEffectiveProvider = (form: EditForm): string =>
    form.provider === CUSTOM_PROVIDER ? form.custom_provider.trim() : form.provider;

  const openEdit = (cfg: AgentEffectiveConfig) => {
    const db = cfg.db_config;
    const savedProvider = db?.provider ?? cfg.effective_provider ?? '';
    const isKnown = KNOWN_PROVIDERS.includes(savedProvider);
    setEditForm({
      provider: isKnown ? savedProvider : (savedProvider ? CUSTOM_PROVIDER : ''),
      custom_provider: isKnown ? '' : savedProvider,
      model_name: db?.model_name ?? cfg.effective_model ?? '',
      temperature: String(db?.temperature ?? cfg.effective_temperature ?? 0),
      api_base_url: db?.api_base_url ?? cfg.effective_api_base_url ?? '',
      api_key_id: db?.api_key_ref ? String(db.api_key_ref.id) : NO_KEY_VALUE,
      description: db?.description ?? '',
    });
    setModalTestResult(null);
    setEditingAgentId(cfg.agent_id);
  };

  const handleSave = async () => {
    if (!editingAgentId) return;
    const effectiveProvider = getEffectiveProvider(editForm);
    if (!effectiveProvider) {
      alert('Please select or enter a provider.');
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        provider: effectiveProvider || null,
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
      const res = await fetch(`${apiBase}/api_keys/agent-configs/${agentId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Reset failed');
      await fetchData();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  // Test from Edit Modal (uses current form values, no save required)
  const handleModalTest = async () => {
    const effectiveProvider = getEffectiveProvider(editForm);
    if (!effectiveProvider) { alert('Please enter a provider first.'); return; }
    setModalTesting(true);
    setModalTestResult(null);
    try {
      const payload: Record<string, unknown> = {
        provider: effectiveProvider,
        model_name: editForm.model_name || null,
        temperature: editForm.temperature !== '' ? parseFloat(editForm.temperature) : 0,
        api_base_url: editForm.api_base_url || null,
        api_key_id: editForm.api_key_id !== NO_KEY_VALUE ? parseInt(editForm.api_key_id, 10) : null,
      };
      const res = await fetch(`${apiBase}/api_keys/test-llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data: TestResult = await res.json();
      setModalTestResult(data);
    } catch (e: any) {
      setModalTestResult({ success: false, message: e.message, latency_ms: null, model_used: null, provider_used: effectiveProvider });
    } finally {
      setModalTesting(false);
    }
  };

  // Test from Agent card (uses effective config already saved)
  const handleCardTest = async (agentId: string) => {
    setCardTestState(prev => ({ ...prev, [agentId]: { loading: true, result: null } }));
    try {
      const res = await fetch(`${apiBase}/api_keys/agent-configs/${agentId}/test`, { method: 'POST' });
      const data: TestResult = await res.json();
      setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: data } }));
      // Auto-clear after 6 seconds
      setTimeout(() => setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: null } })), 6000);
    } catch (e: any) {
      const result: TestResult = { success: false, message: e.message, latency_ms: null, model_used: null, provider_used: agentId };
      setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result } }));
      setTimeout(() => setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: null } })), 6000);
    }
  };

  // Keys filtered by effective provider for dropdown
  const effectiveProviderInForm = getEffectiveProvider(editForm);
  const relevantKeys = effectiveProviderInForm
    ? allKeys.filter(k => k.service_name.toLowerCase() === effectiveProviderInForm.toLowerCase() && k.is_active)
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
        <span className="priority-tip">— 自定義 provider 視為 OpenAI-compatible API</span>
      </div>

      {loading && <div className="agent-loading">LOADING AGENT CONFIGS...</div>}
      {error && <div className="agent-error">⚠ {error}</div>}

      {!loading && !error && (
        <div className="agent-list">
          {configs.map(cfg => {
            const cardState = cardTestState[cfg.agent_id];
            const canTest = cfg.has_db_config || cfg.has_env_override;
            return (
              <div key={cfg.agent_id} className={`agent-card ${cfg.has_db_config ? 'has-db' : ''}`}>
                <div className="agent-card-header">
                  <div className="agent-id-row">
                    <span className="agent-id">{cfg.agent_id}</span>
                    <StatusBadge config={cfg} />
                  </div>
                  <div className="agent-card-actions">
                    {canTest && (
                      <button
                        className="btn btn-test btn-sm"
                        onClick={() => handleCardTest(cfg.agent_id)}
                        disabled={cardState?.loading}
                      >
                        {cardState?.loading ? '...' : '⚡ TEST'}
                      </button>
                    )}
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
                          ? `${cfg.db_config.api_key_ref.service_name} #${cfg.db_config.api_key_ref.id}`
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
                  {cardState?.result && <TestResultDisplay result={cardState.result} />}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Modal */}
      {editingAgentId && (
        <div className="modal-overlay" onClick={() => setEditingAgentId(null)}>
          <div className="agent-modal" onClick={e => e.stopPropagation()}>
            <h3>EDIT: {editingAgentId}</h3>

            <label className="modal-label">PROVIDER</label>
            <select
              value={editForm.provider}
              onChange={e => setEditForm({ ...editForm, provider: e.target.value, custom_provider: '' })}
            >
              <option value="">— inherit global default —</option>
              {KNOWN_PROVIDERS.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
              <option value={CUSTOM_PROVIDER}>── Custom… ──</option>
            </select>

            {editForm.provider === CUSTOM_PROVIDER && (
              <div className="provider-custom-input">
                <input
                  type="text"
                  placeholder="e.g. groq, together, lmstudio, vllm"
                  value={editForm.custom_provider}
                  onChange={e => setEditForm({ ...editForm, custom_provider: e.target.value })}
                  autoFocus
                />
                <span className="provider-custom-hint">
                  ⚠ 自定義 provider 需提供 API Base URL，將以 OpenAI-compatible 方式呼叫
                </span>
              </div>
            )}

            <label className="modal-label">MODEL NAME</label>
            <input
              type="text"
              placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022, llama-3.1-8b-instant"
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
              placeholder="https://api.groq.com/openai/v1"
              value={editForm.api_base_url}
              onChange={e => setEditForm({ ...editForm, api_base_url: e.target.value })}
            />

            <label className="modal-label">
              API KEY REFERENCE
              {effectiveProviderInForm ? ` (${effectiveProviderInForm} keys shown first)` : ' (all active keys)'}
            </label>
            <select
              value={editForm.api_key_id}
              onChange={e => setEditForm({ ...editForm, api_key_id: e.target.value })}
            >
              <option value={NO_KEY_VALUE}>— Use Global Provider Key —</option>
              {relevantKeys.length > 0 && <option disabled>── Matched ──</option>}
              {relevantKeys.map(k => (
                <option key={k.id} value={String(k.id)}>
                  [{k.service_name}] ••••{k.key_value.slice(-4)}
                  {k.description ? ` — ${k.description}` : ''}
                </option>
              ))}
              {/* Show other keys if no match found */}
              {relevantKeys.length === 0 && allKeys.filter(k => k.is_active).map(k => (
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

            {/* Test result display */}
            {modalTestResult && <TestResultDisplay result={modalTestResult} />}

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setEditingAgentId(null)}>
                CANCEL
              </button>
              <button className="btn btn-test" onClick={handleModalTest} disabled={modalTesting}>
                {modalTesting ? 'TESTING...' : '⚡ TEST'}
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
