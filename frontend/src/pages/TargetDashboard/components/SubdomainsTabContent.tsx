import { useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { SkeletonTable } from '../../../components/SkeletonLoader';

interface SubdomainAsset {
  id: number;
  name: string;
  is_active: boolean;
  is_resolvable: boolean;
  is_cdn: boolean;
  is_waf: boolean;
  created_at: string;
  ips: { id: number; address: string }[];
}

type SubSortKey = 'created_at_desc' | 'created_at_asc' | 'name_asc' | 'name_desc';

interface SubdomainsTabContentProps {
  targetId: number;
  subdomains: SubdomainAsset[];
  tabLoading: boolean;
  subTotalCount: number;
  subSortBy: SubSortKey;
  subSearch: string;
  subFilterCdn: boolean | null;
  subFilterWaf: boolean | null;
  subPage: number;
  pageSize: number;
  onFetch: (page: number, sortBy: SubSortKey, search: string, filterCdn: boolean | null, filterWaf: boolean | null) => void;
  onSortChange: (sort: SubSortKey) => void;
  onSearchChange: (search: string) => void;
  onFilterCdnChange: (filter: boolean | null) => void;
  onFilterWafChange: (filter: boolean | null) => void;
}

const SubdomainsTabContent: React.FC<SubdomainsTabContentProps> = ({
  targetId,
  subdomains,
  tabLoading,
  subTotalCount,
  subSortBy,
  subSearch,
  subFilterCdn,
  subFilterWaf,
  subPage,
  pageSize,
  onFetch,
  onSortChange,
  onSearchChange,
  onFilterCdnChange,
  onFilterWafChange,
}) => {
  const navigate = useNavigate();
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const debouncedSearch = useCallback((val: string) => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      onFetch(0, subSortBy, val, subFilterCdn, subFilterWaf);
    }, 350);
  }, [subSortBy, subFilterCdn, subFilterWaf, onFetch]);

  return (
    <>
      <div className="c2-section-header flex-wrap gap-2">
        <span className="c2-section-title">SUBDOMAINS <span>({subTotalCount})</span></span>
        <div className="flex gap-1.5 items-center flex-wrap">
          <input
            className="c2-input w-[190px] text-[0.78rem]"
            placeholder="Search subdomain..."
            value={subSearch}
            onChange={e => { onSearchChange(e.target.value); debouncedSearch(e.target.value); }}
          />
          <button
            className={`c2-btn c2-btn--sm ${subFilterCdn === true ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
            title="Filter: CDN only"
            onClick={() => {
              const next = subFilterCdn === true ? null : true;
              onFilterCdnChange(next);
              onFetch(0, subSortBy, subSearch, next, subFilterWaf);
            }}
          >CDN</button>
          <button
            className={`c2-btn c2-btn--sm ${subFilterWaf === true ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
            title="Filter: WAF only"
            onClick={() => {
              const next = subFilterWaf === true ? null : true;
              onFilterWafChange(next);
              onFetch(0, subSortBy, subSearch, subFilterCdn, next);
            }}
          >WAF</button>
          <select
            className="c2-input w-[155px] text-[0.78rem]"
            value={subSortBy}
            onChange={e => {
              const val = e.target.value as SubSortKey;
              onSortChange(val);
              onFetch(0, val, subSearch, subFilterCdn, subFilterWaf);
            }}
          >
            <option value="created_at_desc">最新優先</option>
            <option value="created_at_asc">最舊優先</option>
            <option value="name_asc">名稱 A→Z</option>
            <option value="name_desc">名稱 Z→A</option>
          </select>
          <button
            className="c2-btn c2-btn--ghost text-[0.7rem]"
            onClick={() => onFetch(subPage, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
          >↻</button>
        </div>
      </div>

      {tabLoading ? (
        <SkeletonTable rows={8} cols={7} />
      ) : subdomains.length === 0 ? (
        <div className="c2-empty">No subdomains found.<br />Run Subfinder on a DOMAIN seed to discover subdomains.</div>
      ) : (
        <div className="c2-card overflow-hidden">
          <table className="c2-table">
            <thead><tr>
              <th>#ID</th><th>SUBDOMAIN</th><th>CDN</th><th>WAF</th>
              <th>RESOLVABLE</th><th>STATUS</th><th>LINKED IPs</th><th>DISCOVERED</th><th></th>
            </tr></thead>
            <tbody>
              {subdomains.map(sub => (
                <tr key={sub.id} onClick={() => navigate(`/target/${targetId}/subdomain/${sub.id}`)} className="cursor-pointer">
                  <td className="td-mono">#{sub.id}</td>
                  <td className="td-mono text-cyan">{sub.name}</td>
                  <td>{sub.is_cdn ? <span className="c2-badge c2-badge--amber">CDN</span> : <span className="td-muted">—</span>}</td>
                  <td>{sub.is_waf ? <span className="c2-badge c2-badge--red">WAF</span> : <span className="td-muted">—</span>}</td>
                  <td>
                    <span className={`c2-badge ${sub.is_resolvable ? 'c2-badge--green' : 'c2-badge--red'}`}>
                      {sub.is_resolvable ? 'YES' : 'NO'}
                    </span>
                  </td>
                  <td>
                    <span className={`c2-badge ${sub.is_active ? 'c2-badge--green' : 'c2-badge--muted'}`}>
                      {sub.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>
                  <td>
                    <div className="flex gap-1 flex-wrap">
                      {sub.ips.length ? sub.ips.map(ip => (
                        <span key={ip.id} className="c2-badge c2-badge--cyan">{ip.address}</span>
                      )) : <span className="td-muted">—</span>}
                    </div>
                  </td>
                  <td className="td-muted">{new Date(sub.created_at).toLocaleDateString()}</td>
                  <td><span className="text-text-muted text-[0.8rem]">→</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!tabLoading && subTotalCount > pageSize && (
        <div className="flex justify-center gap-2 py-3">
          <button
            className="c2-btn c2-btn--ghost text-[0.75rem]"
            onClick={() => onFetch(subPage - 1, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
            disabled={subPage === 0}
          >← PREVIOUS</button>
          <span className="text-[0.75rem] text-text-muted font-mono flex items-center">
            {subPage * pageSize + 1} — {Math.min((subPage + 1) * pageSize, subTotalCount)} / {subTotalCount}
          </span>
          <button
            className="c2-btn c2-btn--ghost text-[0.75rem]"
            onClick={() => onFetch(subPage + 1, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
            disabled={(subPage + 1) * pageSize >= subTotalCount}
          >NEXT →</button>
        </div>
      )}
    </>
  );
};

export default SubdomainsTabContent;
