import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SeedService } from '../../../services/api_seed';
import type { Seed } from '../../../type';

interface SeedsTabContentProps {
  targetId: number;
  seeds: Seed[];
  onRefresh: () => void;
}

const SeedsTabContent: React.FC<SeedsTabContentProps> = ({ targetId, seeds, onRefresh }) => {
  const navigate = useNavigate();
  const [newSeedVal, setNewSeedVal] = useState('');
  const [newSeedType, setNewSeedType] = useState('DOMAIN');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddSeed = async () => {
    if (!newSeedVal.trim()) return;
    setIsAdding(true);
    try {
      await SeedService.add(targetId, { value: newSeedVal.trim(), type: newSeedType });
      setNewSeedVal('');
      onRefresh();
    } catch (e: unknown) {
      alert(`Add failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteSeed = async (seedId: number) => {
    if (!window.confirm('Remove this seed?')) return;
    try {
      await SeedService.delete(seedId);
      onRefresh();
    } catch {
      alert('Delete failed');
    }
  };

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_300px] gap-4 items-start max-md:grid-cols-1">
      <div className="td-seeds-main c2-card p-4">
        <div className="c2-section-header">
          <span className="c2-section-title">SEEDS <span>({seeds.length})</span></span>
          <button className="c2-btn c2-btn--ghost text-[0.7rem]" onClick={onRefresh}>
            Refresh
          </button>
        </div>
        {seeds.length === 0 ? (
          <div className="c2-empty">
            NO SEEDS CONFIGURED.<br />Add a root domain or IP range to begin reconnaissance.
          </div>
        ) : (
          <table className="c2-table">
            <thead>
              <tr>
                <th>#ID</th><th>TYPE</th><th>VALUE</th><th>STATUS</th><th>ADDED</th><th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {seeds.map(seed => (
                <tr key={seed.id}>
                  <td className="td-mono">#{seed.id}</td>
                  <td>
                    <span className={`c2-badge ${seed.type === 'DOMAIN' ? 'c2-badge--green' : seed.type === 'URL' ? 'c2-badge--cyan' : 'c2-badge--amber'}`}>
                      {seed.type}
                    </span>
                  </td>
                  <td className="td-mono">{seed.value}</td>
                  <td>
                    <span className={`c2-badge ${seed.is_active ? 'c2-badge--green' : 'c2-badge--muted'}`}>
                      {seed.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>
                  <td className="td-muted">{new Date(seed.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="flex gap-1.5">
                      {seed.type === 'DOMAIN' && (
                        <button
                          className="c2-btn c2-btn--ghost px-[10px] py-1 text-[0.68rem]"
                          onClick={() => navigate(`/target/${targetId}/seed/${seed.id}/subdomain`)}
                        >
                          RECON
                        </button>
                      )}
                      {seed.type === 'URL' && (
                        <button
                          className="c2-btn c2-btn--ghost px-[10px] py-1 text-[0.68rem]"
                          onClick={() => navigate(`/target/${targetId}/seed/${seed.id}/url_recon`)}
                        >
                          URL RECON
                        </button>
                      )}
                      <button
                        className="c2-btn c2-btn--danger px-2 py-1 text-[0.68rem]"
                        onClick={() => handleDeleteSeed(seed.id)}
                      >×</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="td-seeds-sidebar c2-card c2-card--green p-5">
        <h3 className="font-body text-[0.95rem] mb-4 text-text-primary font-extrabold">
          Add Seed
        </h3>
        <label className="block font-mono text-[0.65rem] text-text-muted uppercase tracking-[0.08em] mb-1.5">Seed Value</label>
        <input
          className="c2-input"
          type="text"
          placeholder="e.g. example.com"
          value={newSeedVal}
          onChange={e => setNewSeedVal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAddSeed()}
        />
        <label className="block font-mono text-[0.65rem] text-text-muted uppercase tracking-[0.08em] mb-1.5">Type</label>
        <select className="c2-select c2-input" value={newSeedType} onChange={e => setNewSeedType(e.target.value)}>
          <option value="DOMAIN">DOMAIN</option>
          <option value="IP_RANGE">IP RANGE</option>
          <option value="URL">URL</option>
        </select>
        <button
          className="c2-btn c2-btn--primary w-full justify-center"
          onClick={handleAddSeed}
          disabled={isAdding || !newSeedVal.trim()}
        >
          {isAdding ? 'Adding...' : 'Add Seed'}
        </button>
        <div className="mt-4 text-[0.72rem] text-text-muted font-mono">
          <div className="mb-2 text-text-secondary">Auto triggers:</div>
          <div>Subdomain Enumeration</div>
          <div>Port Scanning</div>
          <div>AI Initial Analysis</div>
        </div>
      </div>
    </div>
  );
};

export default SeedsTabContent;
