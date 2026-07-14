import { useRef, useCallback } from 'react';
import { SkeletonTable } from '../../../components/SkeletonLoader';
import StatusBadge from './StatusBadge';

interface InitialAIAnalysis {
  id: number;
  risk_score: number;
  summary: string;
  worth_deep_analysis: boolean;
  status: string;
}

interface URLAsset {
  id: number;
  url: string;
  status_code: number;
  title: string;
  content_length: number | null;
  discovery_source: string;
  content_fetch_status: string;
  created_at: string;
  core_initialaianalysis_set?: InitialAIAnalysis[];
}

type URLSortKey = 'created_at_desc' | 'created_at_asc' | 'status_code_asc' | 'preliminary_score_desc' | 'preliminary_score_asc';

interface URLsTabContentProps {
  urls: URLAsset[];
  tabLoading: boolean;
  urlsTotalCount: number;
  urlsSortBy: URLSortKey;
  urlSearch: string;
  urlStatusFilter: string;
  urlsOffset: number;
  pageSize: number;
  onFetch: (offset: number, sortBy: URLSortKey, search: string, statusFilter: string) => void;
  onSortChange: (sort: URLSortKey) => void;
  onSearchChange: (search: string) => void;
  onStatusFilterChange: (filter: string) => void;
}

const URLsTabContent: React.FC<URLsTabContentProps> = ({
  urls,
  tabLoading,
  urlsTotalCount,
  urlsSortBy,
  urlSearch,
  urlStatusFilter,
  urlsOffset,
  pageSize,
  onFetch,
  onSortChange,
  onSearchChange,
  onStatusFilterChange,
}) => {
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const debouncedSearch = useCallback((val: string) => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      onFetch(0, urlsSortBy, val, urlStatusFilter);
    }, 350);
  }, [urlsSortBy, urlStatusFilter, onFetch]);

  const hasFilters = urlSearch || urlStatusFilter;

  return (
    <>
      <div className="c2-section-header flex-wrap gap-2">
        <span className="c2-section-title">URL ASSETS <span>({urlsTotalCount})</span></span>
        <div className="flex gap-1.5 items-center flex-wrap">
          <input
            className="c2-input w-[200px] text-[0.78rem]"
            placeholder="Search URL..."
            value={urlSearch}
            onChange={e => { onSearchChange(e.target.value); debouncedSearch(e.target.value); }}
          />
          <input
            className="c2-input w-[130px] text-[0.78rem]"
            placeholder="Status (e.g. 200)"
            value={urlStatusFilter}
            onChange={e => onStatusFilterChange(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') onFetch(0, urlsSortBy, urlSearch, urlStatusFilter); }}
          />
          {hasFilters && (
            <button
              className="c2-btn c2-btn--ghost text-[0.7rem]"
              onClick={() => {
                onSearchChange('');
                onStatusFilterChange('');
                onFetch(0, urlsSortBy, '', '');
              }}
            >✕ 清除</button>
          )}
          <select
            className="c2-input w-[175px] text-[0.78rem]"
            value={urlsSortBy}
            onChange={e => {
              const val = e.target.value as URLSortKey;
              onSortChange(val);
              onFetch(0, val, urlSearch, urlStatusFilter);
            }}
          >
            <option value="created_at_desc">最新優先 (newest)</option>
            <option value="created_at_asc">最舊優先 (oldest)</option>
            <option value="status_code_asc">狀態碼 (asc)</option>
            <option value="preliminary_score_desc">初步分數 (high→low)</option>
            <option value="preliminary_score_asc">初步分數 (low→high)</option>
          </select>
          <button
            className="c2-btn c2-btn--ghost text-[0.7rem]"
            onClick={() => onFetch(urlsOffset, urlsSortBy, urlSearch, urlStatusFilter)}
          >↻</button>
        </div>
      </div>

      {tabLoading ? (
        <SkeletonTable rows={10} cols={8} />
      ) : urlsTotalCount === 0 ? (
        <div className="c2-empty">No URLs found.<br />Run URL scanning on subdomains to discover endpoints.</div>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="c2-card overflow-hidden">
            <table className="c2-table">
              <thead><tr>
                <th>#ID</th><th>URL</th><th>STATUS</th><th>PRELIMINARY SCORE</th><th>TITLE</th><th>SOURCE</th><th>FETCH STATUS</th><th>FOUND</th><th>DETAIL</th>
              </tr></thead>
              <tbody>
                {urls.map(url => {
                  const preliminaryScore = url.core_initialaianalysis_set?.[0]?.risk_score;
                  return (
                    <tr key={url.id}>
                      <td className="td-mono">#{url.id}</td>
                      <td className="td-mono text-cyan max-w-[280px] overflow-hidden text-ellipsis whitespace-nowrap">
                        <a href={url.url} target="_blank" rel="noopener noreferrer">{url.url}</a>
                      </td>
                      <td>
                        <span className={`c2-badge ${url.status_code >= 200 && url.status_code < 300 ? 'c2-badge--green' : url.status_code >= 300 && url.status_code < 400 ? 'c2-badge--amber' : url.status_code >= 400 ? 'c2-badge--red' : 'c2-badge--muted'}`}>
                          {url.status_code || '—'}
                        </span>
                      </td>
                      <td className="font-mono text-[0.8rem] text-center">
                        {preliminaryScore !== undefined ? (
                          <span style={{ color: preliminaryScore >= 70 ? '#ef4444' : preliminaryScore >= 40 ? '#f59e0b' : '#22C55E' }}>
                            {preliminaryScore.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-text-muted">—</span>
                        )}
                      </td>
                      <td className="max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap text-[0.78rem]">{url.title || '—'}</td>
                      <td className="td-muted">{url.discovery_source}</td>
                      <td><StatusBadge status={url.content_fetch_status} /></td>
                      <td className="td-muted">{new Date(url.created_at).toLocaleDateString()}</td>
                      <td>
                        <a href={`/target/${url.id.split('-')[0] || ''}/url/${url.id}`} className="text-cyan text-[0.72rem] no-underline font-mono">
                          DETAIL →
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex justify-center gap-2 py-3">
            <button
              className="c2-btn c2-btn--ghost text-[0.75rem]"
              onClick={() => onFetch(Math.max(0, urlsOffset - pageSize), urlsSortBy, urlSearch, urlStatusFilter)}
              disabled={urlsOffset === 0}
            >← PREVIOUS</button>
            <span className="text-[0.75rem] text-text-muted font-mono flex items-center">
              {urlsOffset + 1} — {Math.min(urlsOffset + pageSize, urlsTotalCount)} / {urlsTotalCount}
            </span>
            <button
              className="c2-btn c2-btn--ghost text-[0.75rem]"
              onClick={() => onFetch(urlsOffset + pageSize, urlsSortBy, urlSearch, urlStatusFilter)}
              disabled={urlsOffset + pageSize >= urlsTotalCount}
            >NEXT →</button>
          </div>
        </div>
      )}
    </>
  );
};

export default URLsTabContent;
