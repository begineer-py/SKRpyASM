import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Crosshair, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { TargetService, gqlFetcher, GET_TARGETS_QUERY } from '../services/targetApi';
import type { Target } from '../types';

function IndexPage() {
  const navigate = useNavigate();

  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const fetchTargets = async () => {
    setLoading(true);
    try {
      const data = await gqlFetcher<{ core_target: Target[] }>(GET_TARGETS_QUERY);
      setTargets(data.core_target);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '無法連接至 Hasura API，請確認 Docker 服務狀態。');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newName.trim()) return;
    try {
      await TargetService.create({ name: newName, description: newDesc });
      setNewName('');
      setNewDesc('');
      fetchTargets(); 
    } catch (err) {
      console.error(err);
      alert('新增失敗: 請檢查後端日誌');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('【警告】確定刪除此專案？\n所有關聯的域名、掃描結果將永久消失。')) return;
    try {
      await TargetService.delete(id);
      fetchTargets();
    } catch (err) {
      console.error(err);
      alert('刪除失敗');
    }
  };

  const startEdit = (t: Target) => {
    setEditingId(t.id);
    setEditName(t.name);
    setEditDesc(t.description || '');
  };


  useEffect(() => {
    fetchTargets();
  }, []);

  return (
    <div className="c2-page target-list-page">
      <header className="target-hero">
        <div>
          <div className="target-hero__eyebrow"><Crosshair size={14} /> Operations / command surface</div>
          <h1>Attack Surface <em>Control</em></h1>
          <p>Manage authorized targets, scope, and reconnaissance state from one operations view.</p>
        </div>
        <div className="target-hero__signal"><span className="c2-pulse" /><span><strong>Live telemetry</strong><small>Command channel online</small></span></div>
      </header>
      
      {error && (
        <div className="mb-[18px] px-3.5 py-3 border border-[rgba(239,68,68,0.28)] rounded-[14px] bg-[rgba(239,68,68,0.10)] text-[#fecaca]">
          <strong>CONNECTION ERROR:</strong> {error}
        </div>
      )}

      <div className="grid grid-cols-[minmax(0,1fr)_minmax(300px,360px)] gap-5 items-start max-[980px]:grid-cols-1">
        
        {/* 左側：目標列表區域 */}
        <section className="target-panel">
          <div className="target-panel__header">
            <div><span className="c2-kicker">Authorized scope</span><h2>Active targets <b>{targets.length.toString().padStart(2, '0')}</b></h2></div>
            <button className="c2-btn c2-btn--ghost c2-btn--sm" onClick={fetchTargets} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> {loading ? 'Syncing...' : 'Refresh'}
            </button>
          </div>
          
          {targets.length === 0 && !loading ? (
            <div className="target-empty">
              <Crosshair size={28} /><h3>No Active Operations</h3>
              <p>Create a new target on the right to begin reconnaissance.</p>
            </div>
          ) : (
            <ul className="target-grid">
              {targets.map(t => (
                <li key={t.id} className="target-card">
                  <div className="target-card__topline"><span className="target-card__index">0{t.id}</span><span className="target-card__id">ID / {t.id}</span></div>
                  <div className="target-card__heading">
                    <span>{t.name}</span>
                    <span className="c2-badge c2-badge--green">active</span>
                  </div>
                  <div className="target-card__description">
                    {t.description || 'No description provided.'}
                  </div>
                  <div className="target-card__date">Registered {new Date(t.created_at).toLocaleDateString()}</div>

                  <div className="target-card__actions">
                    <button className="c2-btn c2-btn--primary" onClick={() => navigate(`/target/${t.id}`)}>
                      Open operation <ArrowUpRight size={15} />
                    </button>
                    <button className="c2-btn c2-btn--icon" aria-label={`Edit ${t.name}`} onClick={() => startEdit(t)}>
                      <Pencil size={14} />
                    </button>
                    <button className="c2-btn c2-btn--icon c2-btn--danger-icon" aria-label={`Delete ${t.name}`} onClick={() => handleDelete(t.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* 右側：操作面板 */}
        <aside className="target-form-panel">
          {editingId ? (
            <>
              <div className="target-form-panel__heading"><span className="c2-kicker">Scope mutation</span><h3>Editing target <b>#{editingId}</b></h3></div>
              
              <div className="mb-3.5">
                <label className="c2-form-label">Project name</label>
                <input
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)]"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                />
              </div>
              
              <div className="mb-3.5">
                <label className="c2-form-label">Description</label>
                <textarea
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)] resize-y min-h-[96px]"
                  rows={3}
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                />
              </div>
              
              <div className="target-form-panel__actions">
                <button className="c2-btn c2-btn--primary w-full">Save changes</button>
                <button className="c2-btn c2-btn--ghost w-full" onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </>
          ) : (
            <>
              <div className="target-form-panel__heading"><span className="c2-kicker">New workspace</span><h3>Create target</h3></div>
              
              <div className="mb-3.5">
                <label className="c2-form-label">Project name</label><input
                  type="text"
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)]"
                  placeholder="Target Name (e.g. SpaceX)"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                />
              </div>
              
              <div className="mb-3.5">
                <label className="c2-form-label">Mission description</label><textarea
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)] resize-y min-h-[96px]"
                  placeholder="Mission Description / Scope"
                  rows={3}
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                />
              </div>
              
              <button className="c2-btn c2-btn--success w-full" onClick={handleAdd}>
                <Plus size={16} /> Create target
              </button>
              
              <div className="target-form-panel__workflow">
                <strong>Workflow</strong><span>01 / Create a container</span><span>02 / Open the operation</span><span>03 / Add seeds and assets</span>
              </div>
            </>
          )}
        </aside>

      </div>
    </div>
  );
}

export default IndexPage;
