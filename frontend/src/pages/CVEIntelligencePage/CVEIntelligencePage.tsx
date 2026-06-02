import { useState } from 'react';
import { CVEService, type CVEIntelligence } from '../../services/api_cve';
import CVECard from '../../components/CVECard';

type SearchMode = 'cve_id' | 'tech_search';
type SeverityFilter = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | '';

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

  // Tech search mode
  const [techName, setTechName] = useState('');
  const [version, setVersion] = useState('');
  const [severityMin, setSeverityMin] = useState<SeverityFilter>('');
  const [exploitedOnly, setExploitedOnly] = useState(false);
  const [limit, setLimit] = useState(20);
  const [pubStartDate, setPubStartDate] = useState('');
  const [pubEndDate, setPubEndDate] = useState('');
  const [minCvss, setMinCvss] = useState('');
  const [minEpss, setMinEpss] = useState('');

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
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 20px 40px', paddingTop: 'calc(var(--navbar-height) + 24px)' }}>
      {/* Page header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '1.1rem',
            color: 'var(--text-green)',
            margin: 0,
            letterSpacing: '0.06em',
          }}>
            CVE INTELLIGENCE CENTER
          </h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
            Query CVE details or search by technology stack
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <button
            className="c2-btn c2-btn--sm"
            onClick={handleSyncKEV}
            disabled={syncing}
          >
            {syncing ? 'SYNCING...' : '🔄 SYNC CISA KEV'}
          </button>
          {syncMsg && (
            <span style={{ fontSize: '0.7rem', color: syncMsg.startsWith('Sync failed') ? 'var(--red)' : 'var(--text-green)' }}>
              {syncMsg}
            </span>
          )}
        </div>
      </div>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button
          className={`c2-btn c2-btn--sm${mode === 'tech_search' ? ' c2-btn--active' : ''}`}
          onClick={() => { setMode('tech_search'); setResults([]); setTotal(null); setError(null); }}
          style={{ opacity: mode === 'tech_search' ? 1 : 0.5 }}
        >
          Tech Stack Search
        </button>
        <button
          className={`c2-btn c2-btn--sm${mode === 'cve_id' ? ' c2-btn--active' : ''}`}
          onClick={() => { setMode('cve_id'); setResults([]); setTotal(null); setError(null); }}
          style={{ opacity: mode === 'cve_id' ? 1 : 0.5 }}
        >
          CVE ID Lookup
        </button>
      </div>

      {/* Search form */}
      <div className="c2-card" style={{ padding: '16px', marginBottom: 20 }}>
        {mode === 'cve_id' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                className="c2-input"
                style={{ flex: 1, fontFamily: 'var(--font-mono)' }}
                placeholder="CVE-2021-44228"
                value={cveIdInput}
                onChange={e => setCveIdInput(e.target.value)}
                onKeyDown={handleKeyDown}
                spellCheck={false}
              />
              <button
                className="c2-btn"
                onClick={handleCveQuery}
                disabled={loading || !cveIdInput.trim()}
              >
                {loading ? 'QUERYING...' : 'QUERY'}
              </button>
            </div>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              userSelect: 'none',
            }}>
              <input
                type="checkbox"
                checked={useNvd}
                onChange={e => setUseNvd(e.target.checked)}
              />
              <span>
                Query NVD if not in local DB
                {!useNvd && (
                  <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>
                    (local DB only)
                  </span>
                )}
              </span>
            </label>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Primary inputs */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <input
                className="c2-input"
                style={{ flex: 2, minWidth: 160 }}
                placeholder="Technology name (e.g. apache, nginx, log4j)"
                value={techName}
                onChange={e => setTechName(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <input
                className="c2-input"
                style={{ flex: 1, minWidth: 100 }}
                placeholder="Version (optional)"
                value={version}
                onChange={e => setVersion(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>

            {/* Filters row 1: severity + limit + exploited */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                className="c2-input"
                style={{ width: 150 }}
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
                className="c2-input"
                style={{ width: 110 }}
                value={limit}
                onChange={e => setLimit(Number(e.target.value))}
              >
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
                <option value={50}>50 results</option>
                <option value={100}>100 results</option>
              </select>

              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={exploitedOnly}
                  onChange={e => setExploitedOnly(e.target.checked)}
                />
                Exploited Only
              </label>
            </div>

            {/* Filters row 2: cvss/epss + date range + submit */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Min CVSS</span>
                <input
                  className="c2-input"
                  type="number"
                  min={0} max={10} step={0.1}
                  placeholder="0–10"
                  style={{ width: 75 }}
                  value={minCvss}
                  onChange={e => setMinCvss(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Min EPSS</span>
                <input
                  className="c2-input"
                  type="number"
                  min={0} max={1} step={0.01}
                  placeholder="0–1"
                  style={{ width: 75 }}
                  value={minEpss}
                  onChange={e => setMinEpss(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Published after</span>
                <input
                  className="c2-input"
                  type="date"
                  style={{ width: 140 }}
                  value={pubStartDate}
                  onChange={e => setPubStartDate(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>before</span>
                <input
                  className="c2-input"
                  type="date"
                  style={{ width: 140 }}
                  value={pubEndDate}
                  onChange={e => setPubEndDate(e.target.value)}
                />
              </div>
              <button
                className="c2-btn"
                onClick={handleTechSearch}
                disabled={loading || !techName.trim()}
                style={{ marginLeft: 'auto' }}
              >
                {loading ? 'SEARCHING...' : 'SEARCH'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{ color: 'var(--red)', fontSize: '0.85rem', marginBottom: 16, padding: '10px 14px', border: '1px solid var(--red)', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {/* Results header */}
      {total !== null && !loading && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12, fontFamily: 'var(--font-mono)' }}>
          {total === 0
            ? 'No CVEs found.'
            : `${results.length} / ${total} CVE${total !== 1 ? 's' : ''} — click a card to expand details`}
        </div>
      )}

      {/* Results list */}
      {results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {results.map(cve => (
            <CVECard key={cve.id ?? cve.cve_id} cve={cve} />
          ))}
        </div>
      )}

      {/* Empty state (before first search) */}
      {total === null && !loading && !error && (
        <div style={{
          textAlign: 'center',
          padding: '48px 20px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          border: '1px dashed var(--border-color)',
          borderRadius: 6,
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 12 }}>🛡️</div>
          {mode === 'cve_id'
            ? 'Enter a CVE ID to query its details'
            : 'Enter a technology name to find related CVEs'}
        </div>
      )}
    </div>
  );
}
