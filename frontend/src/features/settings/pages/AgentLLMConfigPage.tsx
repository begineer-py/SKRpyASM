import { useState, useEffect } from 'react';
import { GLOBAL_CONFIG } from '../../../config';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

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
  provider: string;
  custom_provider: string;
  model_name: string;
  temperature: string;
  api_base_url: string;
  api_key_id: string;
  description: string;
}

const KNOWN_PROVIDERS = ['openai', 'anthropic', 'mistral', 'deepseek', 'opencode', 'ollama'];
const CUSTOM_PROVIDER = '__custom__';
const NO_KEY_VALUE = '__none__';
const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

const PROVIDER_HINTS: Record<string, { hint: string; defaultBaseUrl?: string; defaultModel?: string }> = {
  opencode: {
    hint: '✦ OpenCode Zen Gateway — OpenAI-compatible，支援 deepseek-v4-flash / deepseek-v4-pro 等模型',
    defaultBaseUrl: 'https://opencode.ai/zen/go/v1',
    defaultModel: 'deepseek-v4-flash',
  },
  openai: { hint: 'OpenAI 官方 API', defaultModel: 'gpt-4o' },
  anthropic: { hint: 'Anthropic Claude API', defaultModel: 'claude-sonnet-4-6' },
  mistral: { hint: 'Mistral AI API', defaultModel: 'mistral-small-2603' },
  deepseek: { hint: 'DeepSeek 官方 API', defaultBaseUrl: 'https://api.deepseek.com/v1', defaultModel: 'deepseek-chat' },
  ollama: { hint: '本地 Ollama 服務（無需 API Key）', defaultBaseUrl: 'http://localhost:11434', defaultModel: 'llama3' },
};

function StatusBadge({ config }: { config: AgentEffectiveConfig }) {
  if (config.has_db_config) {
    return <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-green-900 text-green-300 border border-green-800">CONFIGURED</span>;
  }
  return <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-500 border border-slate-700">DEFAULT</span>;
}

function TestResultDisplay({ result }: { result: TestResult }) {
  const icon = result.success ? '✓' : '✗';
  const latency = result.latency_ms != null ? ` — ${result.latency_ms}ms` : '';
  const msg = result.message.length > 120 ? result.message.slice(0, 120) + '…' : result.message;
  return (
    <div className={cn(
      "text-xs mt-2.5 px-3 py-2 rounded leading-relaxed break-words",
      result.success
        ? "bg-green-900 text-green-300 border border-green-800"
        : "bg-[#450a0a] text-red-300 border border-red-900"
    )}>
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

  const [modalTesting, setModalTesting] = useState(false);
  const [modalTestResult, setModalTestResult] = useState<TestResult | null>(null);

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
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load agent configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

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
    } catch (e: unknown) {
      alert(`Error: ${e instanceof Error ? e.message : 'Save failed'}`);
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
    } catch (e: unknown) {
      alert(`Error: ${e instanceof Error ? e.message : 'Reset failed'}`);
    }
  };

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
    } catch (e: unknown) {
      setModalTestResult({ success: false, message: e instanceof Error ? e.message : 'Test failed', latency_ms: null, model_used: null, provider_used: effectiveProvider });
    } finally {
      setModalTesting(false);
    }
  };

  const handleCardTest = async (agentId: string) => {
    setCardTestState(prev => ({ ...prev, [agentId]: { loading: true, result: null } }));
    try {
      const res = await fetch(`${apiBase}/api_keys/agent-configs/${agentId}/test`, { method: 'POST' });
      const data: TestResult = await res.json();
      setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: data } }));
      setTimeout(() => setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: null } })), 6000);
    } catch (e: unknown) {
      const result: TestResult = { success: false, message: e instanceof Error ? e.message : 'Test failed', latency_ms: null, model_used: null, provider_used: agentId };
      setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result } }));
      setTimeout(() => setCardTestState(prev => ({ ...prev, [agentId]: { loading: false, result: null } })), 6000);
    }
  };

  const effectiveProviderInForm = getEffectiveProvider(editForm);
  const relevantKeys = effectiveProviderInForm
    ? allKeys.filter(k => k.service_name.toLowerCase() === effectiveProviderInForm.toLowerCase() && k.is_active)
    : allKeys.filter(k => k.is_active);

  const modalInputCls = "w-full mb-1 px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-md text-slate-200 font-mono text-[13px] outline-none box-border";
  const modalLabelCls = "block text-[10px] text-slate-500 mb-1 mt-3 tracking-[0.8px]";

  return (
    <div className="c2-page min-h-screen text-text-primary font-body text-base">
      <div className="flex justify-between items-center mb-4">
        <div className="flex flex-col">
          <h1 className="text-[28px] font-bold tracking-[2px] m-0 text-slate-100">
            <span className="text-slate-500">[</span>
            AGENT_LLM_CONFIG
            <span className="text-slate-500">]</span>
          </h1>
          <span className="text-[13px] text-slate-500 mt-1">
            Agent 獨立模型配置 — DB 覆蓋 / Env Var / 全域默認
          </span>
        </div>
        <button className="px-[18px] py-2 rounded-md text-[13px] font-semibold cursor-pointer border border-slate-600 transition-all duration-200 bg-[#1e2937] text-slate-200 hover:bg-slate-700" onClick={fetchData} disabled={loading}>
          {loading ? '...' : '↺ REFRESH'}
        </button>
      </div>

      {/* Priority Legend */}
      <div className="bg-[#1e2937] border border-slate-600 rounded-lg px-5 py-2.5 mb-6 flex items-center gap-2.5 flex-wrap">
        <span className="text-slate-500 text-[11px] tracking-[1px] mr-1">PRIORITY:</span>
        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-green-900 text-green-300 border border-green-800">CONFIGURED</span>
        <span className="text-slate-600 text-sm">&gt;</span>
        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-500 border border-slate-700">DEFAULT</span>
        <span className="text-slate-500 text-[11px] ml-2">— 在 EDIT 中設定後生效；自定義 provider 視為 OpenAI-compatible API</span>
      </div>

      {loading && <div className="text-center py-[60px] px-5 text-slate-500 text-sm">LOADING AGENT CONFIGS...</div>}
      {error && <div className="text-center py-[60px] px-5 text-red-500 text-sm">⚠ {error}</div>}

      {!loading && !error && (
        <div className="flex flex-col gap-3">
          {configs.map(cfg => {
            const cardState = cardTestState[cfg.agent_id];
            const canTest = cfg.has_db_config || cfg.has_env_override;
            return (
              <div key={cfg.agent_id} className={cn(
                "bg-[#1e2937] border border-slate-600 rounded-lg overflow-hidden transition-colors duration-200",
                cfg.has_db_config && "border-green-800"
              )}>
                <div className="px-5 py-3.5 flex justify-between items-center border-b border-slate-600">
                  <div className="flex items-center gap-3">
                    <span className="text-[15px] font-bold text-slate-100 tracking-[0.5px]">{cfg.agent_id}</span>
                    <StatusBadge config={cfg} />
                  </div>
                  <div className="flex gap-2">
                    {canTest && (
                      <button
                        className="px-3 py-1 text-xs rounded-md font-semibold cursor-pointer border transition-all duration-200 bg-[#1e3a5f] text-cyan-300 border-[#1e4d7b] hover:bg-[#1e4d7b] hover:text-cyan-200 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed"
                        onClick={() => handleCardTest(cfg.agent_id)}
                        disabled={cardState?.loading}
                      >
                        {cardState?.loading ? '...' : '⚡ TEST'}
                      </button>
                    )}
                    <button className="px-3 py-1 text-xs rounded-md font-semibold cursor-pointer border border-slate-600 transition-all duration-200 bg-[#1e2937] text-slate-200 hover:bg-slate-700" onClick={() => openEdit(cfg)}>
                      EDIT
                    </button>
                    {cfg.has_db_config && (
                      <button className="px-3 py-1 text-xs rounded-md font-semibold cursor-pointer border transition-all duration-200 bg-[#1e2937] text-red-400 border-red-900 hover:bg-red-900 hover:text-red-300" onClick={() => handleReset(cfg.agent_id)}>
                        RESET
                      </button>
                    )}
                  </div>
                </div>

                <div className="px-5 py-3.5 bg-slate-900">
                  <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-x-6 gap-y-3">
                    <div className="flex flex-col gap-[3px]">
                      <span className="text-[10px] text-slate-500 tracking-[1px]">PROVIDER</span>
                      <span className="text-[13px] text-cyan-300 uppercase">{cfg.effective_provider}</span>
                    </div>
                    <div className="flex flex-col gap-[3px]">
                      <span className="text-[10px] text-slate-500 tracking-[1px]">MODEL</span>
                      <span className="text-[13px] text-purple-300">{cfg.effective_model}</span>
                    </div>
                    <div className="flex flex-col gap-[3px]">
                      <span className="text-[10px] text-slate-500 tracking-[1px]">TEMP</span>
                      <span className="text-[13px] text-slate-400">{cfg.effective_temperature.toFixed(1)}</span>
                    </div>
                    <div className="flex flex-col gap-[3px]">
                      <span className="text-[10px] text-slate-500 tracking-[1px]">API KEY</span>
                      <span className="text-[13px] text-amber-400">
                        {cfg.db_config?.api_key_ref
                          ? `${cfg.db_config.api_key_ref.service_name} #${cfg.db_config.api_key_ref.id}`
                          : '— global fallback —'}
                      </span>
                    </div>
                    {cfg.effective_api_base_url && (
                      <div className="flex flex-col gap-[3px] col-span-full">
                        <span className="text-[10px] text-slate-500 tracking-[1px]">BASE URL</span>
                        <span className="text-slate-400 text-xs break-all">{cfg.effective_api_base_url}</span>
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
      <Dialog open={!!editingAgentId} onOpenChange={(open) => { if (!open) setEditingAgentId(null); }}>
        <DialogContent className="bg-bg-elevated border-border-subtle text-text-primary max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-text-primary font-body">EDIT: {editingAgentId}</DialogTitle>
          </DialogHeader>

          <label className={modalLabelCls}>PROVIDER</label>
          <select
            className={modalInputCls}
            value={editForm.provider}
            onChange={e => {
              const newProvider = e.target.value;
              const hint = PROVIDER_HINTS[newProvider];
              setEditForm(prev => ({
                ...prev,
                provider: newProvider,
                custom_provider: '',
                api_base_url: prev.api_base_url || (hint?.defaultBaseUrl ?? ''),
              }));
            }}
          >
            <option value="">— inherit global default —</option>
            {KNOWN_PROVIDERS.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
            <option value={CUSTOM_PROVIDER}>── Custom… ──</option>
          </select>

          {KNOWN_PROVIDERS.includes(editForm.provider) && PROVIDER_HINTS[editForm.provider] && (
            <span className="block text-[11px] text-amber-500 mt-1 mb-2" style={{ color: editForm.provider === 'opencode' ? '#7c3aed' : undefined }}>
              {PROVIDER_HINTS[editForm.provider].hint}
            </span>
          )}

          {editForm.provider === CUSTOM_PROVIDER && (
            <div className="mb-1">
              <input
                className={modalInputCls}
                type="text"
                placeholder="e.g. groq, together, lmstudio, vllm"
                value={editForm.custom_provider}
                onChange={e => setEditForm({ ...editForm, custom_provider: e.target.value })}
                autoFocus
              />
              <span className="block text-[11px] text-amber-500 mt-1 mb-2">
                ⚠ 自定義 provider 需提供 API Base URL，將以 OpenAI-compatible 方式呼叫
              </span>
            </div>
          )}

          <label className={modalLabelCls}>MODEL NAME</label>
          <input
            className={modalInputCls}
            type="text"
            placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022, llama-3.1-8b-instant"
            value={editForm.model_name}
            onChange={e => setEditForm({ ...editForm, model_name: e.target.value })}
          />

          <label className={modalLabelCls}>TEMPERATURE (0.0 – 2.0)</label>
          <input
            className={modalInputCls}
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={editForm.temperature}
            onChange={e => setEditForm({ ...editForm, temperature: e.target.value })}
          />

          <label className={modalLabelCls}>API BASE URL (optional)</label>
          <input
            className={modalInputCls}
            type="text"
            placeholder={
              PROVIDER_HINTS[editForm.provider]?.defaultBaseUrl ??
              'https://api.groq.com/openai/v1'
            }
            value={editForm.api_base_url}
            onChange={e => setEditForm({ ...editForm, api_base_url: e.target.value })}
          />

          <label className={modalLabelCls}>
            API KEY REFERENCE
            {effectiveProviderInForm ? ` (${effectiveProviderInForm} keys shown first)` : ' (all active keys)'}
          </label>
          <select
            className={modalInputCls}
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
            {relevantKeys.length === 0 && allKeys.filter(k => k.is_active).map(k => (
              <option key={k.id} value={String(k.id)}>
                [{k.service_name}] ••••{k.key_value.slice(-4)}
                {k.description ? ` — ${k.description}` : ''}
              </option>
            ))}
          </select>

          <label className={modalLabelCls}>DESCRIPTION (optional)</label>
          <input
            className={modalInputCls}
            type="text"
            placeholder="e.g. Uses GPT-4o for complex exploit analysis"
            value={editForm.description}
            onChange={e => setEditForm({ ...editForm, description: e.target.value })}
          />

          {modalTestResult && <TestResultDisplay result={modalTestResult} />}

          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditingAgentId(null)}>
              CANCEL
            </Button>
            <Button variant="secondary" onClick={handleModalTest} disabled={modalTesting}>
              {modalTesting ? 'TESTING...' : '⚡ TEST'}
            </Button>
            <Button variant="default" onClick={handleSave} disabled={saving}>
              {saving ? 'SAVING...' : 'SAVE CONFIG'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AgentLLMConfigPage;
