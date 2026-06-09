import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// 注意路徑：回到 src 根目錄找 services 和 type
import { TargetService, gqlFetcher, GET_TARGETS_QUERY } from '../../services/api';
import type { Target } from '../../type';
import './indexPage.css';

function IndexPage() {
  const navigate = useNavigate();

  // 數據與狀態
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 表單輸入 (新增)
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  
  // 表單輸入 (編輯)
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  // === 讀取 (Read) via GraphQL ===
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

  // === 寫入 (Write) via Django API ===
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

  // 初始化
  useEffect(() => {
    fetchTargets();
  }, []);

  return (
    <div className="c2-page dashboard-container">
      <header className="dashboard-header">
        <div>
          <div className="eyebrow">Operations</div>
          <h1>Attack Surface Control</h1>
          <p>Manage authorized targets, scope, and reconnaissance state from one operations view.</p>
        </div>
        <div className="status-badge">Live telemetry</div>
      </header>
      
      {/* 錯誤橫幅 */}
      {error && (
        <div className="error-banner">
          <strong>CONNECTION ERROR:</strong> {error}
        </div>
      )}

      <div className="dashboard-layout">
        
        {/* 左側：目標列表區域 */}
        <div className="target-list-section">
          <div className="section-header">
            <h2 style={{ margin: 0 }}>Active Targets <span>{targets.length}</span></h2>
            <button className="btn btn-ghost btn-sm" onClick={fetchTargets} disabled={loading}>
              {loading ? 'Syncing...' : 'Refresh'}
            </button>
          </div>
          
          {targets.length === 0 && !loading ? (
            <div className="empty-state">
              <h3>No Active Operations</h3>
              <p>Create a new target on the right to begin reconnaissance.</p>
            </div>
          ) : (
            <ul className="target-list">
              {targets.map(t => (
                <li key={t.id} className="target-card">
                  <div className="card-header">
                    <span className="target-name">{t.name}</span>
                    <span className="target-id">ID: {t.id}</span>
                  </div>
                  
                  <div className="target-desc">
                    {t.description || 'No description provided.'}
                  </div>
                  
                  <div style={{fontSize: '0.8rem', color: '#666', marginBottom: '10px'}}>
                     Created: {new Date(t.created_at).toLocaleString()}
                  </div>

                  <div className="card-actions">
                    <button 
                      className="btn btn-primary" 
                      onClick={() => navigate(`/target/${t.id}`)}
                    >
                      Open Operation
                    </button>
                    
                    <button 
                      className="btn btn-warning btn-sm" 
                      onClick={() => startEdit(t)}
                    >
                      Edit
                    </button>
                    
                    <button 
                      className="btn btn-danger btn-sm" 
                      style={{marginLeft: 'auto'}}
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
        <aside className="action-panel">
          {editingId ? (
            // === 編輯模式 ===
            <>
              <h3 className="panel-title editing">Editing Target #{editingId}</h3>
              
              <div className="form-group">
                <label>Project Name</label>
                <input 
                  className="input-field" 
                  value={editName} 
                  onChange={e => setEditName(e.target.value)} 
                />
              </div>
              
              <div className="form-group">
                <label>Description</label>
                <textarea 
                  className="input-field" 
                  rows={3} 
                  value={editDesc} 
                  onChange={e => setEditDesc(e.target.value)} 
                />
              </div>
              
              <div style={{display: 'flex', gap: '10px'}}>
                <button className="btn btn-warning btn-block" onClick={handleUpdate}>Save Changes</button>
                <button className="btn btn-ghost btn-block" onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </>
          ) : (
            // === 新增模式 ===
            <>
              <h3 className="panel-title">New Operation</h3>
              
              <div className="form-group">
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Target Name (e.g. SpaceX)" 
                  value={newName} 
                  onChange={e => setNewName(e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <textarea 
                  className="input-field" 
                  placeholder="Mission Description / Scope" 
                  rows={3} 
                  value={newDesc} 
                  onChange={e => setNewDesc(e.target.value)}
                />
              </div>
              
              <button className="btn btn-success btn-block" onClick={handleAdd}>
                Create Target
              </button>
              
              <div style={{marginTop: '20px', fontSize: '0.8rem', color: '#666', borderTop: '1px solid #333', paddingTop: '10px'}}>
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
