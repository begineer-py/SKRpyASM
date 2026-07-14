import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TargetService, gqlFetcher, GET_TARGETS_QUERY } from '../../../services/api';
import type { Target } from '../../../type';
import { cn } from '@/lib/utils';

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
    } catch (err: any) {
      setError(err.message || '無法連接至 Hasura API，請確認 Docker 服務狀態。');
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

  const handleUpdate = async () => {
    if (editingId === null) return;
    try {
      await TargetService.update(editingId, { name: editName, description: editDesc });
      setEditingId(null);
      fetchTargets();
    } catch (err) {
      console.error(err);
      alert('更新失敗');
    }
  };

  useEffect(() => {
    fetchTargets();
  }, []);

  const btnBase = "inline-flex items-center justify-center gap-1.5 px-3.5 py-[9px] border border-transparent rounded-[11px] cursor-pointer font-body text-[0.82rem] font-extrabold transition-all duration-200";
  const btnSm = "px-[10px] py-[7px] text-[0.76rem]";

  return (
    <div className="c2-page max-w-[1440px]">
      <header
        className="grid grid-cols-[minmax(0,1fr)_auto] gap-6 items-end mb-7 p-[34px] border border-border-subtle rounded-[24px] shadow-soft overflow-hidden relative max-sm:grid-cols-1 max-sm:p-6"
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(5, 8, 20, 0.64)), radial-gradient(circle at 12% 18%, rgba(59, 130, 246, 0.18), transparent 30rem)'
        }}
      >
        <div>
          <div className="mb-2 text-cyan font-mono text-[0.72rem] font-bold tracking-[0.16em] uppercase">Operations</div>
          <h1 className="m-0 max-w-[780px] text-text-primary font-extrabold" style={{ fontSize: 'clamp(2rem, 4vw, 4.5rem)', lineHeight: 0.95 }}>Attack Surface Control</h1>
          <p className="max-w-[650px] mt-4 mx-0 text-text-secondary text-base">Manage authorized targets, scope, and reconnaissance state from one operations view.</p>
        </div>
        <div className="inline-flex items-center gap-2 self-start px-3 py-[9px] border border-[rgba(34,197,94,0.22)] rounded-full bg-[rgba(34,197,94,0.08)] text-[#86efac] font-mono text-[0.72rem] font-bold tracking-widest uppercase before:content-[''] before:w-[7px] before:h-[7px] before:rounded-full before:bg-green-500 before:shadow-[0_0_10px_rgba(34,197,94,0.55)]">Live telemetry</div>
        <div className="absolute inset-x-[34px] bottom-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(96, 165, 250, 0.42), transparent)' }} />
      </header>
      
      {error && (
        <div className="mb-[18px] px-3.5 py-3 border border-[rgba(239,68,68,0.28)] rounded-[14px] bg-[rgba(239,68,68,0.10)] text-[#fecaca]">
          <strong>CONNECTION ERROR:</strong> {error}
        </div>
      )}

      <div className="grid grid-cols-[minmax(0,1fr)_minmax(300px,360px)] gap-5 items-start max-[980px]:grid-cols-1">
        
        {/* 左側：目標列表區域 */}
        <div className="border border-border-subtle rounded-[20px] bg-[rgba(10,15,29,0.74)] shadow-soft backdrop-blur-[12px] p-[18px]">
          <div className="flex justify-between items-center gap-4 mb-4 px-1 pt-1 pb-4 border-b border-border-subtle">
            <h2 className="text-text-primary text-base font-extrabold tracking-tight m-0">Active Targets <span className="ml-2 text-cyan font-mono text-[0.78rem]">{targets.length}</span></h2>
            <button className={cn(btnBase, btnSm, "bg-[rgba(15,23,42,0.38)] border-border-subtle text-text-secondary hover:border-border-normal hover:text-text-primary")} onClick={fetchTargets} disabled={loading}>
              {loading ? 'Syncing...' : 'Refresh'}
            </button>
          </div>
          
          {targets.length === 0 && !loading ? (
            <div className="px-6 py-[54px] border border-dashed border-[rgba(148,163,184,0.20)] rounded-[18px] text-text-secondary text-center">
              <h3 className="mb-1.5 text-text-primary">No Active Operations</h3>
              <p>Create a new target on the right to begin reconnaissance.</p>
            </div>
          ) : (
            <ul className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-3.5 list-none p-0 m-0 max-sm:grid-cols-1">
              {targets.map(t => (
                <li
                  key={t.id}
                  className="min-h-[210px] flex flex-col p-[18px] border border-[rgba(148,163,184,0.13)] rounded-[18px] relative overflow-hidden transition-all duration-200 hover:-translate-y-px hover:border-[rgba(96,165,250,0.34)] before:content-[''] before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:opacity-70"
                  style={{ background: 'linear-gradient(180deg, rgba(18, 24, 38, 0.92), rgba(11, 17, 31, 0.88))' }}
                >
                  <div className="flex justify-between items-start gap-3.5 mb-3">
                    <span className="text-text-primary text-[1.12rem] font-extrabold tracking-tight">{t.name}</span>
                    <span className="px-2 py-[3px] border border-[rgba(148,163,184,0.15)] rounded-full text-text-secondary bg-[rgba(15,23,42,0.74)] font-mono text-[0.68rem] whitespace-nowrap">ID: {t.id}</span>
                  </div>
                  
                  <div className="flex-1 text-text-secondary text-[0.92rem] leading-[1.55]">
                    {t.description || 'No description provided.'}
                  </div>
                  
                  <div className="text-[0.8rem] text-[#666] mb-2.5">
                     Created: {new Date(t.created_at).toLocaleString()}
                  </div>

                  <div className="flex gap-2 items-center mt-4 pt-3.5 border-t border-[rgba(148,163,184,0.10)] max-sm:flex-wrap">
                    <button
                      className={cn(btnBase, "bg-[rgba(59,130,246,0.18)] border-[rgba(96,165,250,0.30)] text-[#bfdbfe] hover:bg-[rgba(59,130,246,0.28)]")}
                      onClick={() => navigate(`/target/${t.id}`)}
                    >
                      Open Operation
                    </button>
                    
                    <button
                      className={cn(btnBase, btnSm, "bg-[rgba(245,158,11,0.14)] border-[rgba(245,158,11,0.28)] text-[#fde68a]")}
                      onClick={() => startEdit(t)}
                    >
                      Edit
                    </button>
                    
                    <button
                      className={cn(btnBase, btnSm, "bg-[rgba(239,68,68,0.11)] border-[rgba(239,68,68,0.24)] text-[#fecaca] ml-auto")}
                      onClick={() => handleDelete(t.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 右側：操作面板 */}
        <aside className="border border-border-subtle rounded-[20px] bg-[rgba(10,15,29,0.74)] shadow-soft backdrop-blur-[12px] p-[22px] max-[980px]:static sticky" style={{ top: 'calc(var(--navbar-height) + 60px)' }}>
          {editingId ? (
            <>
              <h3 className="m-0 mb-[18px] pb-3.5 border-b border-border-subtle text-amber-400 text-base font-extrabold">Editing Target #{editingId}</h3>
              
              <div className="mb-3.5">
                <label className="block mb-[7px] text-text-secondary font-mono text-[0.68rem] font-bold tracking-widest uppercase">Project Name</label>
                <input
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)]"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                />
              </div>
              
              <div className="mb-3.5">
                <label className="block mb-[7px] text-text-secondary font-mono text-[0.68rem] font-bold tracking-widest uppercase">Description</label>
                <textarea
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)] resize-y min-h-[96px]"
                  rows={3}
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                />
              </div>
              
              <div className="flex gap-2.5">
                <button className={cn(btnBase, "w-full mt-2.5 bg-[rgba(245,158,11,0.14)] border-[rgba(245,158,11,0.28)] text-[#fde68a]")}>Save Changes</button>
                <button className={cn(btnBase, "w-full mt-2.5 bg-[rgba(15,23,42,0.38)] border-border-subtle text-text-secondary hover:border-border-normal hover:text-text-primary")} onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </>
          ) : (
            <>
              <h3 className="m-0 mb-[18px] pb-3.5 border-b border-border-subtle text-text-primary text-base font-extrabold">New Operation</h3>
              
              <div className="mb-3.5">
                <input
                  type="text"
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)]"
                  placeholder="Target Name (e.g. SpaceX)"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                />
              </div>
              
              <div className="mb-3.5">
                <textarea
                  className="w-full px-3 py-[10px] border border-border-subtle rounded-xl bg-[rgba(5,8,20,0.68)] text-text-primary font-body outline-none transition-all duration-200 focus:border-border-strong focus:bg-[rgba(8,13,27,0.94)] focus:shadow-[0_0_0_3px_var(--blue-glow)] resize-y min-h-[96px]"
                  placeholder="Mission Description / Scope"
                  rows={3}
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                />
              </div>
              
              <button className={cn(btnBase, "w-full mt-2.5 bg-[rgba(34,197,94,0.16)] border-[rgba(34,197,94,0.30)] text-[#bbf7d0] hover:bg-[rgba(34,197,94,0.25)]")} onClick={handleAdd}>
                Create Target
              </button>
              
              <div className="mt-5 text-[0.8rem] text-[#666] border-t border-[#333] pt-2.5">
                <p><strong>Workflow:</strong></p>
                1. Create a container here.<br/>
                2. Open the operation dashboard.<br/>
                3. Add Seeds (Domains/IPs) inside.
              </div>
            </>
          )}
        </aside>

      </div>
    </div>
  );
}

export default IndexPage;
