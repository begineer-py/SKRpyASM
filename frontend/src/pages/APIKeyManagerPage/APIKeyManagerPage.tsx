import { useState, useEffect } from 'react';
import { GLOBAL_CONFIG } from '../../config';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface APIKey {
  id: number;
  service_name: string;
  key_value: string;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

interface BulkKey {
  service_name: string;
  key_value: string;
  description?: string;
}

const CUSTOM_OPTION = '__custom__';
const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

function ServiceSelect({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  const [services, setServices] = useState<string[]>([
    "shodan", "securitytrails", "censys", "chaos", "dnsdb",
    "virustotal", "binaryedge", "zoomeye", "fofa", "github",
    "hunter", "urlscan", "alienvault", "threatcrowd",
    "passivetotal", "riskiq", "intelx", "fullhunt", "quake",
    "netlas", "publicwww",
  ]);
  const [isCustom, setIsCustom] = useState(false);

  useEffect(() => {
    fetch(`${apiBase}/api_keys/supported-services`)
      .then(r => r.json())
      .then(data => { if (Array.isArray(data)) setServices(data); })
      .catch(() => {});
  }, []);

  if (isCustom) {
    return (
      <div className="flex gap-2 items-center mb-3">
        <input
          className="flex-1 mb-0 w-full px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-md text-slate-200 text-sm"
          type="text"
          placeholder="Type custom service name..."
          value={value}
          onChange={e => onChange(e.target.value)}
          autoFocus
        />
        <button className="px-2.5 py-1.5 bg-[#1e2937] border border-slate-600 rounded text-slate-400 text-[11px] cursor-pointer whitespace-nowrap hover:bg-slate-700 hover:text-slate-200" onClick={() => { setIsCustom(false); onChange(''); }}>
          ← BACK TO LIST
        </button>
      </div>
    );
  }

  return (
    <select
      className="w-full mb-3 px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-md text-slate-200 text-sm cursor-pointer"
      value={value}
      onChange={e => {
        if (e.target.value === CUSTOM_OPTION) {
          setIsCustom(true);
          onChange('');
        } else {
          onChange(e.target.value);
        }
      }}
    >
      <option value="" disabled>{placeholder}</option>
      {services.map(s => (
        <option key={s} value={s}>{s}</option>
      ))}
      <option value={CUSTOM_OPTION}>── Custom… ──</option>
    </select>
  );
}

const APIKeyManagerPage: React.FC = () => {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);

  const [newKey, setNewKey] = useState({ service_name: '', key_value: '', description: '' });
  const [bulkText, setBulkText] = useState('');
  const [bulkService, setBulkService] = useState('');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api_keys/`);
      if (!res.ok) throw new Error('Failed to fetch API keys');
      const data: APIKey[] = await res.json();
      setKeys(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const groupedKeys = keys.reduce((acc, key) => {
    const svc = key.service_name.toLowerCase();
    if (!acc[svc]) acc[svc] = [];
    acc[svc].push(key);
    return acc;
  }, {} as Record<string, APIKey[]>);

  const services = Object.keys(groupedKeys).sort();

  const maskKey = (key: string) => {
    if (key.length <= 8) return '••••••••';
    return '••••••••' + key.slice(-4);
  };

  const handleCopy = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleToggleActive = async (key: APIKey) => {
    try {
      const res = await fetch(`${apiBase}/api_keys/${key.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !key.is_active }),
      });
      if (!res.ok) throw new Error('Update failed');
      await fetchKeys();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  const handleDelete = async (id: number, service: string) => {
    if (!confirm(`Delete key for ${service}?`)) return;
    try {
      const res = await fetch(`${apiBase}/api_keys/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      await fetchKeys();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  const handleAddSingle = async () => {
    if (!newKey.service_name || !newKey.key_value) {
      alert('Service name and key value are required');
      return;
    }
    try {
      const res = await fetch(`${apiBase}/api_keys/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_name: newKey.service_name.trim(),
          key_value: newKey.key_value.trim(),
          description: newKey.description.trim() || null,
          is_active: true,
        }),
      });
      if (!res.ok) throw new Error('Create failed');
      setNewKey({ service_name: '', key_value: '', description: '' });
      setShowAddModal(false);
      await fetchKeys();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  const handleBulkImport = async () => {
    if (!bulkService || !bulkText.trim()) {
      alert('Service name and keys are required');
      return;
    }
    const lines = bulkText.trim().split('\n').filter(l => l.trim());
    const payload: BulkKey[] = lines.map(line => ({
      service_name: bulkService.trim(),
      key_value: line.trim(),
      description: 'Bulk imported',
    }));
    try {
      const res = await fetch(`${apiBase}/api_keys/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Bulk import failed');
      setBulkText('');
      setBulkService('');
      setShowBulkModal(false);
      await fetchKeys();
      alert(`Imported ${payload.length} keys for ${bulkService}`);
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  const downloadConfig = async (tool: string) => {
    try {
      const res = await fetch(`${apiBase}/api_keys/download?tool=${tool}`);
      if (!res.ok) throw new Error(`Download ${tool} failed`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${tool}-config.${tool === 'subfinder' ? 'yaml' : tool === 'amass' ? 'ini' : tool === 'gau' ? 'toml' : 'yaml'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`Download error: ${e.message}`);
    }
  };

  const modalInputCls = "w-full mb-3 px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-md text-slate-200 text-sm";
  const modalLabelCls = "block text-[11px] text-slate-500 mb-1 mt-2 tracking-[0.5px]";

  return (
    <div className="pt-20 px-6 pb-6 max-w-[1400px] mx-auto text-slate-200 font-mono">
      <div className="flex justify-between items-center mb-4">
        <div className="flex flex-col">
          <h1 className="text-[28px] font-bold tracking-[2px] m-0 text-slate-100">
            <span className="text-slate-500">[</span>
            API_KEY_MANAGER
            <span className="text-slate-500">]</span>
          </h1>
          <span className="text-[13px] text-slate-500 mt-1">外部服務金鑰管理 — 多金鑰輪轉 / 配置下載</span>
        </div>
        <div className="flex gap-3">
          <button className="px-[18px] py-2 rounded-md text-[13px] font-semibold cursor-pointer border border-slate-600 transition-all duration-200 bg-[#1e2937] text-slate-200 hover:bg-slate-700" onClick={() => setShowBulkModal(true)}>
            📥 BULK IMPORT
          </button>
          <button className="px-[18px] py-2 rounded-md text-[13px] font-semibold cursor-pointer border border-blue-500 transition-all duration-200 bg-blue-500 text-white hover:bg-blue-600" onClick={() => setShowAddModal(true)}>
            ＋ ADD KEY
          </button>
        </div>
      </div>

      <div className="bg-[#1e2937] border border-slate-600 rounded-lg px-5 py-3 mb-6 flex items-center gap-3 flex-wrap">
        <span className="text-slate-500 text-xs mr-2">DOWNLOAD CONFIGS →</span>
        <button className="px-3.5 py-1.5 bg-slate-900 border border-slate-600 rounded text-slate-400 text-xs cursor-pointer transition-all duration-200 hover:bg-[#1e2937] hover:text-slate-200 hover:border-blue-500" onClick={() => downloadConfig('subfinder')}>subfinder</button>
        <button className="px-3.5 py-1.5 bg-slate-900 border border-slate-600 rounded text-slate-400 text-xs cursor-pointer transition-all duration-200 hover:bg-[#1e2937] hover:text-slate-200 hover:border-blue-500" onClick={() => downloadConfig('amass')}>amass</button>
        <button className="px-3.5 py-1.5 bg-slate-900 border border-slate-600 rounded text-slate-400 text-xs cursor-pointer transition-all duration-200 hover:bg-[#1e2937] hover:text-slate-200 hover:border-blue-500" onClick={() => downloadConfig('gau')}>gau</button>
        <button className="px-3.5 py-1.5 bg-slate-900 border border-slate-600 rounded text-slate-400 text-xs cursor-pointer transition-all duration-200 hover:bg-[#1e2937] hover:text-slate-200 hover:border-blue-500" onClick={() => downloadConfig('nuclei')}>nuclei</button>
      </div>

      {loading && <div className="text-center px-5 py-[60px] text-slate-500 text-sm">LOADING KEYS FROM DB...</div>}
      {error && <div className="text-center px-5 py-[60px] text-red-500 text-sm">⚠ {error}</div>}

      {!loading && !error && services.length === 0 && (
        <div className="text-center px-5 py-[60px] text-slate-500 text-sm">NO API KEYS CONFIGURED. ADD YOUR FIRST KEY ABOVE.</div>
      )}

      <div className="flex flex-col gap-3">
        {services.map(service => {
          const serviceKeys = groupedKeys[service];
          const activeCount = serviceKeys.filter(k => k.is_active).length;
          const isExpanded = selectedService === service;

          return (
            <div key={service} className="bg-[#1e2937] border border-slate-600 rounded-lg overflow-hidden">
              <div
                className="px-5 py-3.5 flex justify-between items-center cursor-pointer transition-colors duration-200 hover:bg-slate-700"
                onClick={() => setSelectedService(isExpanded ? null : service)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-base font-bold text-slate-100">{service.toUpperCase()}</span>
                  <span className="text-xs px-2 py-0.5 bg-slate-900 rounded-full text-slate-500">{activeCount}/{serviceKeys.length} ACTIVE</span>
                </div>
                <div className="flex items-center gap-3 text-slate-500 text-[13px]">
                  <span>{serviceKeys.length} keys</span>
                  <span className="text-[11px]">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t border-slate-600 bg-slate-900">
                  {serviceKeys.map(key => (
                    <div key={key.id} className={cn(
                      "px-5 py-3 flex justify-between items-center border-b border-slate-600 last:border-b-0",
                      !key.is_active && "opacity-60"
                    )}>
                      <div className="flex flex-col gap-0.5">
                        <span className="font-mono text-slate-400 cursor-pointer text-sm relative hover:text-slate-200" onClick={() => handleCopy(key.key_value, key.id)}>
                          {maskKey(key.key_value)}
                          {copiedId === key.id && <span className="absolute left-full ml-2 text-green-500 text-[11px]">COPIED!</span>}
                        </span>
                        {key.description && <span className="text-xs text-slate-500">{key.description}</span>}
                      </div>
                      <div className="flex gap-2">
                        <button
                          className={cn(
                            "px-2.5 py-1 text-[11px] rounded border cursor-pointer",
                            key.is_active
                              ? "bg-green-800 text-green-300 border-green-800"
                              : "border-slate-600 bg-[#1e2937] text-slate-500"
                          )}
                          onClick={() => handleToggleActive(key)}
                        >
                          {key.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </button>
                        <button className="bg-transparent border-none text-slate-500 cursor-pointer text-sm px-1.5 py-0.5 hover:text-red-500" onClick={() => handleDelete(key.id, service)}>🗑</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add Single Modal */}
      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent className="bg-bg-elevated border-border-subtle text-text-primary max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-text-primary font-body">ADD NEW API KEY</DialogTitle>
          </DialogHeader>

          <label className={modalLabelCls}>SERVICE NAME</label>
          <ServiceSelect
            value={newKey.service_name}
            onChange={v => setNewKey({ ...newKey, service_name: v })}
            placeholder="Select a service…"
          />

          <label className={modalLabelCls}>API KEY VALUE</label>
          <input
            className={modalInputCls}
            type="text"
            placeholder="Paste your API key here"
            value={newKey.key_value}
            onChange={e => setNewKey({ ...newKey, key_value: e.target.value })}
          />

          <label className={modalLabelCls}>DESCRIPTION (optional)</label>
          <input
            className={modalInputCls}
            type="text"
            placeholder="e.g. Shodan API (Premium)"
            value={newKey.description}
            onChange={e => setNewKey({ ...newKey, description: e.target.value })}
          />

          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowAddModal(false)}>CANCEL</Button>
            <Button variant="default" onClick={handleAddSingle}>ADD KEY</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Import Modal */}
      <Dialog open={showBulkModal} onOpenChange={setShowBulkModal}>
        <DialogContent className="bg-bg-elevated border-border-subtle text-text-primary max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-text-primary font-body">BULK IMPORT KEYS</DialogTitle>
          </DialogHeader>

          <label className={modalLabelCls}>SERVICE NAME</label>
          <ServiceSelect
            value={bulkService}
            onChange={setBulkService}
            placeholder="Select a service…"
          />

          <label className={modalLabelCls}>KEYS (ONE PER LINE)</label>
          <textarea
            className="w-full mb-3 px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-md text-slate-200 text-sm resize-y min-h-[120px]"
            placeholder="key1&#10;key2&#10;key3"
            value={bulkText}
            onChange={e => setBulkText(e.target.value)}
            rows={8}
          />

          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowBulkModal(false)}>CANCEL</Button>
            <Button variant="default" onClick={handleBulkImport}>IMPORT</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default APIKeyManagerPage;
