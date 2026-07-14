import { useState } from 'react';
import { CVEService, type CVEIntelligence } from '../services/scannerApi';
import CVECard from '../../../components/CVECard';

type SearchMode = 'cve_id' | 'tech_search';
type SeverityFilter = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | '';

const DEFAULT_FILTERS = {
  severityMin: '' as SeverityFilter,
  exploitedOnly: false,
  limit: 20,
  pubStartDate: '',
  pubEndDate: '',
  minCvss: '',
  minEpss: '',
};

export default function CVEIntelligencePage() {
  const [mode, setMode] = useState<SearchMode>('tech_search');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CVEIntelligence[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  // NVD fallback toggle (只在 CVE ID 查詢模式下有效)
  const [useNvd, setUseNvd] = useState(true);

  // CVE ID mode
  const [cveIdInput, setCveIdInput] = useState('');

  // Tech search mode — basic inputs always visible
  const [techName, setTechName] = useState('');
  const [version, setVersion] = useState('');

  // Advanced filters (collapsible)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [severityMin, setSeverityMin] = useState<SeverityFilter>(DEFAULT_FILTERS.severityMin);
  const [exploitedOnly, setExploitedOnly] = useState(DEFAULT_FILTERS.exploitedOnly);
  const [limit, setLimit] = useState(DEFAULT_FILTERS.limit);
  const [pubStartDate, setPubStartDate] = useState(DEFAULT_FILTERS.pubStartDate);
  const [pubEndDate, setPubEndDate] = useState(DEFAULT_FILTERS.pubEndDate);
  const [minCvss, setMinCvss] = useState(DEFAULT_FILTERS.minCvss);
  const [minEpss, setMinEpss] = useState(DEFAULT_FILTERS.minEpss);

  const isAdvancedDirty = severityMin !== DEFAULT_FILTERS.severityMin
    || exploitedOnly !== DEFAULT_FILTERS.exploitedOnly
    || limit !== DEFAULT_FILTERS.limit
    || pubStartDate !== ''
    || pubEndDate !== ''
    || minCvss !== ''
    || minEpss !== '';

  const handleClearFilters = () => {
    setSeverityMin(DEFAULT_FILTERS.severityMin);
    setExploitedOnly(DEFAULT_FILTERS.exploitedOnly);
    setLimit(DEFAULT_FILTERS.limit);
    setPubStartDate(DEFAULT_FILTERS.pubStartDate);
    setPubEndDate(DEFAULT_FILTERS.pubEndDate);
    setMinCvss(DEFAULT_FILTERS.minCvss);
    setMinEpss(DEFAULT_FILTERS.minEpss);
  };

  const handleCveQuery = async () => {
    const trimmed = cveIdInput.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setTotal(null);
    try {
      const cve = await CVEService.queryCVE(trimmed, useNvd);
      setResults([cve]);
      setTotal(1);
    } catch (e: unknown) {
      const axiosErr = e as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 404) {
        setError(`CVE "${trimmed}" not found in the database.`);
      } else {
        setError(e instanceof Error ? e.message : 'Query failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTechSearch = async () => {
    if (!techName.trim()) return;

    // Date range validation
    if (pubStartDate && pubEndDate && pubEndDate < pubStartDate) {
      setError('結束日期不可早於開始日期');
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);
    setTotal(null);
    try {
      const data = await CVEService.searchCVEs({
        tech_name: techName.trim(),
        version: version.trim() || undefined,
        severity_min: severityMin || undefined,
        exploited_only: exploitedOnly || undefined,
        limit,
        pub_start_date: pubStartDate || undefined,
        pub_end_date: pubEndDate || undefined,
        min_cvss: minCvss ? parseFloat(minCvss) : undefined,
        min_epss: minEpss ? parseFloat(minEpss) : undefined,
      });
      setResults(data.cves);
      setTotal(data.total);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncKEV = async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await CVEService.syncKEV();
      setSyncMsg(res.detail || 'CISA KEV sync task dispatched.');
      setTimeout(() => setSyncMsg(null), 5000);
    } catch (e: unknown) {
      setSyncMsg(e instanceof Error ? `Sync failed: ${e.message}` : 'Sync failed');
      setTimeout(() => setSyncMsg(null), 5000);
    } finally {
      setSyncing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (mode === 'cve_id') handleCveQuery();
      else handleTechSearch();
    }
  };

  return (
    <div className="max-w-[900px] mx-auto px-5 pb-10" style={{ paddingTop: 'calc(var(--navbar-height) + 24px)' }}>
      {/* Page header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="font-mono text-[1.1rem] text-green m-0 tracking-[0.06em]">
            CVE INTELLIGENCE CENTER
          </h1>
          <p className="text-[0.75rem] text-text-muted mt-1">
            Query CVE details or search by technology stack
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button className="c2-btn c2-btn--sm" onClick={handleSyncKEV} disabled={syncing}>
            {syncing ? 'SYNCING...' : '🔄 SYNC CISA KEV'}
          </button>
          {syncMsg && (
            <span className="text-[0.7rem]" style={{ color: syncMsg.startsWith('Sync failed') ? 'var(--red)' : 'var(--text-green)' }}>
              {syncMsg}
            </span>
          )}
        </div>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-4">
        <button
          className={`c2-btn c2-btn--sm${mode === 'tech_search' ? ' c2-btn--active' : ''}`}
          onClick={() => { setMode('tech_search'); setResults([]); setTotal(null); setError(null); }}
          style={{ opacity: mode === 'tech_search' ? 1 : 0.5 }}
        >Tech Stack Search</button>
        <button
          className={`c2-btn c2-btn--sm${mode === 'cve_id' ? ' c2-btn--active' : ''}`}
          onClick={() => { setMode('cve_id'); setResults([]); setTotal(null); setError(null); }}
          style={{ opacity: mode === 'cve_id' ? 1 : 0.5 }}
        >CVE ID Lookup</button>
      </div>

      {/* Search form */}
      <div className="c2-card p-4 mb-5">
        {mode === 'cve_id' ? (
          <div className="flex flex-col gap-2.5">
            <div className="flex gap-2.5 items-center">
              <input
                className="c2-input flex-1 font-mono"
                placeholder="CVE-2021-44228"
                value={cveIdInput}
                onChange={e => setCveIdInput(e.target.value)}
                onKeyDown={handleKeyDown}
                spellCheck={false}
              />
              <button className="c2-btn" onClick={handleCveQuery} disabled={loading || !cveIdInput.trim()}>
                {loading ? 'QUERYING...' : 'QUERY'}
              </button>
            </div>
            <label className="flex items-center gap-1.5 text-[0.78rem] text-text-secondary cursor-pointer select-none">
              <input type="checkbox" checked={useNvd} onChange={e => setUseNvd(e.target.checked)} />
              <span>
                Query NVD if not in local DB
                {!useNvd && <span className="text-text-muted ml-1.5">(local DB only)</span>}
              </span>
            </label>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {/* Primary inputs + submit */}
            <div className="flex gap-2.5 flex-wrap items-center">
              <input
                className="c2-input flex-[2] min-w-[160px]"
                placeholder="Technology name (e.g. apache, nginx, log4j)"
                value={techName}
                onChange={e => setTechName(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <input
                className="c2-input flex-1 min-w-[100px]"
                placeholder="Version (optional)"
                value={version}
                onChange={e => setVersion(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button className="c2-btn" onClick={handleTechSearch} disabled={loading || !techName.trim()}>
                {loading ? 'SEARCHING...' : 'SEARCH'}
              </button>
            </div>

            {/* Advanced filters toggle */}
            <div className="flex items-center gap-2">
              <button
                className="c2-btn c2-btn--ghost c2-btn--sm text-[0.75rem]"
                onClick={() => setShowAdvanced(v => !v)}
              >
                {showAdvanced ? '▲ 隱藏進階篩選' : '▼ 進階篩選'}
                {isAdvancedDirty && !showAdvanced && (
                  <span className="ml-1.5 text-amber text-[0.7rem]">● 已設定</span>
                )}
              </button>
              {isAdvancedDirty && (
                <button
                  className="c2-btn c2-btn--ghost c2-btn--sm text-[0.72rem] text-text-muted"
                  onClick={handleClearFilters}
                >✕ 清除篩選</button>
              )}
            </div>

            {/* Advanced filters panel */}
            {showAdvanced && (
              <div className="flex flex-col gap-2.5 p-3 bg-[rgba(15,23,42,0.5)] rounded border border-border-subtle">
                {/* Row 1: Severity + Limit + Exploited */}
                <div className="flex gap-2.5 items-center flex-wrap">
                  <select
                    className="c2-input w-[150px]"
                    value={severityMin}
                    onChange={e => setSeverityMin(e.target.value as SeverityFilter)}
                  >
                    <option value="">All Severities</option>
                    <option value="CRITICAL">CRITICAL+</option>
                    <option value="HIGH">HIGH+</option>
                    <option value="MEDIUM">MEDIUM+</option>
                    <option value="LOW">LOW+</option>
                  </select>
                  <select
                    className="c2-input w-[110px]"
                    value={limit}
                    onChange={e => setLimit(Number(e.target.value))}
                  >
                    <option value={10}>10 results</option>
                    <option value={20}>20 results</option>
                    <option value={50}>50 results</option>
                    <option value={100}>100 results</option>
                  </select>
                  <label className="flex items-center gap-1.5 text-[0.8rem] text-text-secondary cursor-pointer">
                    <input type="checkbox" checked={exploitedOnly} onChange={e => setExploitedOnly(e.target.checked)} />
                    Exploited Only
                  </label>
                </div>

                {/* Row 2: CVSS + EPSS */}
                <div className="flex gap-2.5 items-center flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[0.72rem] text-text-muted whitespace-nowrap">Min CVSS</span>
                    <input
                      className="c2-input w-[75px]"
                      type="number"
                      min={0} max={10} step={0.1}
                      placeholder="0–10"
                      value={minCvss}
                      onChange={e => setMinCvss(e.target.value)}
                    />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[0.72rem] text-text-muted whitespace-nowrap">Min EPSS</span>
                    <input
                      className="c2-input w-[75px]"
                      type="number"
                      min={0} max={1} step={0.01}
                      placeholder="0–1"
                      value={minEpss}
                      onChange={e => setMinEpss(e.target.value)}
                    />
                  </div>
                </div>

                {/* Row 3: Date range */}
                <div className="flex gap-2.5 items-center flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[0.72rem] text-text-muted whitespace-nowrap">Published after</span>
                    <input
                      className="c2-input w-[140px]"
                      type="date"
                      value={pubStartDate}
                      onChange={e => setPubStartDate(e.target.value)}
                    />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[0.72rem] text-text-muted whitespace-nowrap">before</span>
                    <input
                      className="c2-input w-[140px]"
                      type="date"
                      value={pubEndDate}
                      onChange={e => setPubEndDate(e.target.value)}
                    />
                  </div>
                  {pubStartDate && pubEndDate && pubEndDate < pubStartDate && (
                    <span className="text-[0.72rem] text-red">⚠ 結束日期不可早於開始日期</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="text-red text-[0.85rem] mb-4 px-[14px] py-[10px] border border-red rounded">
          {error}
        </div>
      )}

      {/* Results header */}
      {total !== null && !loading && (
        <div className="text-[0.75rem] text-text-muted mb-3 font-mono">
          {total === 0
            ? 'No CVEs found.'
            : `顯示 ${results.length} / ${total} 筆 CVE${total !== 1 ? 's' : ''} — 點擊卡片展開詳情`}
        </div>
      )}

      {/* Results list */}
      {results.length > 0 && (
        <div className="flex flex-col gap-2">
          {results.map(cve => (
            <CVECard key={cve.id ?? cve.cve_id} cve={cve} />
          ))}
        </div>
      )}

      {/* Empty state (before first search) */}
      {total === null && !loading && !error && (
        <div className="text-center px-5 py-12 text-text-muted font-mono text-[0.8rem] border border-dashed border-[var(--border-color)] rounded-[6px]">
          <div className="text-[2rem] mb-3">🛡️</div>
          {mode === 'cve_id'
            ? 'Enter a CVE ID to query its details'
            : 'Enter a technology name to find related CVEs'}
        </div>
      )}
    </div>
  );
}
