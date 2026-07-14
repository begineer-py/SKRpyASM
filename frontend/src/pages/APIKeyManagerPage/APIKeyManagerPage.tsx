import { useState, useEffect } from 'react';
import { GLOBAL_CONFIG } from '../../config';
import './APIKeyManager.css';
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
      <div className="service-select-wrapper">
        <input
          type="text"
          placeholder="Type custom service name..."
          value={value}
          onChange={e => onChange(e.target.value)}
          autoFocus
        />
        <button className="btn-back" onClick={() => { setIsCustom(false); onChange(''); }}>
          ← BACK TO LIST
        </button>
      </div>
    );
  }

  return (
    <select
      className="service-select"
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

  return (
    <div className="c2-page apikey-container">
      <div className="apikey-header">
        <div className="apikey-header-left">
          <h1 className="apikey-title">
            <span className="apikey-bracket">[</span>
            API_KEY_MANAGER
            <span className="apikey-bracket">]</span>
          </h1>
          <span className="apikey-subtitle">外部服務金鑰管理 — 多金鑰輪轉 / 配置下載</span>
        </div>
        <div className="apikey-actions">
          <button className="btn btn-secondary" onClick={() => setShowBulkModal(true)}>
            📥 BULK IMPORT
          </button>
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            ＋ ADD KEY
          </button>
        </div>
      </div>

      <div className="apikey-download-bar">
        <span className="download-label">DOWNLOAD CONFIGS →</span>
        <button className="btn-download" onClick={() => downloadConfig('subfinder')}>subfinder</button>
        <button className="btn-download" onClick={() => downloadConfig('amass')}>amass</button>
        <button className="btn-download" onClick={() => downloadConfig('gau')}>gau</button>
        <button className="btn-download" onClick={() => downloadConfig('nuclei')}>nuclei</button>
      </div>

      {loading && <div className="apikey-loading">LOADING KEYS FROM DB...</div>}
      {error && <div className="apikey-error">⚠ {error}</div>}

      {!loading && !error && services.length === 0 && (
        <div className="apikey-empty">NO API KEYS CONFIGURED. ADD YOUR FIRST KEY ABOVE.</div>
      )}

      <div className="apikey-services">
        {services.map(service => {
          const serviceKeys = groupedKeys[service];
          const activeCount = serviceKeys.filter(k => k.is_active).length;
          const isExpanded = selectedService === service;

          return (
            <div key={service} className="service-card">
              <div
                className="service-header"
                onClick={() => setSelectedService(isExpanded ? null : service)}
              >
                <div className="service-info">
                  <span className="service-name">{service.toUpperCase()}</span>
                  <span className="service-count">{activeCount}/{serviceKeys.length} ACTIVE</span>
                </div>
                <div className="service-meta">
                  <span className="service-total">{serviceKeys.length} keys</span>
                  <span className="service-arrow">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="service-keys">
                  {serviceKeys.map(key => (
                    <div key={key.id} className={`key-row ${!key.is_active ? 'inactive' : ''}`}>
                      <div className="key-main">
                        <span className="key-masked" onClick={() => handleCopy(key.key_value, key.id)}>
                          {maskKey(key.key_value)}
                          {copiedId === key.id && <span className="copied">COPIED!</span>}
                        </span>
                        {key.description && <span className="key-desc">{key.description}</span>}
                      </div>
                      <div className="key-actions">
                        <button
                          className={`btn-toggle ${key.is_active ? 'active' : ''}`}
                          onClick={() => handleToggleActive(key)}
                        >
                          {key.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </button>
                        <button className="btn-icon" onClick={() => handleDelete(key.id, service)}>🗑</button>
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

          <label className="modal-label">SERVICE NAME</label>
          <ServiceSelect
            value={newKey.service_name}
            onChange={v => setNewKey({ ...newKey, service_name: v })}
            placeholder="Select a service…"
          />

          <label className="modal-label">API KEY VALUE</label>
          <input
            type="text"
            placeholder="Paste your API key here"
            value={newKey.key_value}
            onChange={e => setNewKey({ ...newKey, key_value: e.target.value })}
          />

          <label className="modal-label">DESCRIPTION (optional)</label>
          <input
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

          <label className="modal-label">SERVICE NAME</label>
          <ServiceSelect
            value={bulkService}
            onChange={setBulkService}
            placeholder="Select a service…"
          />

          <label className="modal-label">KEYS (ONE PER LINE)</label>
          <textarea
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