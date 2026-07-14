import { useState } from 'react';
import { SkeletonCards } from '../../../components/SkeletonLoader';
import StatusBadge from './StatusBadge';

interface Port {
  id: number;
  port_number: number;
  protocol: string;
  service_name: string;
  service_version: string;
  state: string;
  first_seen?: string;
}

interface IPAsset {
  id: number;
  address: string;
  version: number | null;
  ports: Port[];
}

type IPSortKey = 'id_desc' | 'address_asc' | 'address_desc';

interface IPsTabContentProps {
  ips: IPAsset[];
  tabLoading: boolean;
  ipTotalCount: number;
  ipSortBy: IPSortKey;
  ipPortFilter: string;
  ipPage: number;
  pageSize: number;
  onFetch: (page: number, sortBy: IPSortKey, portFilter: string) => void;
  onSortChange: (sort: IPSortKey) => void;
  onPortFilterChange: (filter: string) => void;
}

const IPsTabContent: React.FC<IPsTabContentProps> = ({
  ips,
  tabLoading,
  ipTotalCount,
  ipSortBy,
  ipPortFilter,
  ipPage,
  pageSize,
  onFetch,
  onSortChange,
  onPortFilterChange,
}) => {
  const [expandedIp, setExpandedIp] = useState<number | null>(null);

  return (
    <>
      <div className="c2-section-header flex-wrap gap-2">
        <span className="c2-section-title">IP ASSETS <span>({ipTotalCount})</span></span>
        <div className="flex gap-1.5 items-center flex-wrap">
          <input
            className="c2-input w-[190px] text-[0.78rem]"
            placeholder="Filter by port (e.g. 443)"
            value={ipPortFilter}
            onChange={e => onPortFilterChange(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') onFetch(0, ipSortBy, ipPortFilter); }}
          />
          <button
            className="c2-btn c2-btn--ghost text-[0.7rem]"
            onClick={() => onFetch(0, ipSortBy, ipPortFilter)}
          >FILTER</button>
          {ipPortFilter && (
            <button
              className="c2-btn c2-btn--ghost text-[0.7rem]"
              onClick={() => { onPortFilterChange(''); onFetch(0, ipSortBy, ''); }}
            >\u2715</button>
          )}
          <select
            className="c2-input w-[155px] text-[0.78rem]"
            value={ipSortBy}
            onChange={e => {
              const val = e.target.value as IPSortKey;
              onSortChange(val);
              onFetch(0, val, ipPortFilter);
            }}
          >
            <option value="id_desc">\u6700\u65B0\u65B0\u589E</option>
            <option value="address_asc">IP \u4F4D\u5740 A\u2192Z</option>
            <option value="address_desc">IP \u4F4D\u5740 Z\u2192A</option>
          </select>
          <button
            className="c2-btn c2-btn--ghost text-[0.7rem]"
            onClick={() => onFetch(ipPage, ipSortBy, ipPortFilter)}
          >\u21BB</button>
        </div>
      </div>

      {tabLoading ? (
        <SkeletonCards count={6} height={52} />
      ) : ips.length === 0 ? (
        <div className="c2-empty">No IP assets found.<br />Run Nmap on seeds to discover IP addresses and open ports.</div>
      ) : (
        <div className="flex flex-col gap-2">
          {ips.map(ip => (
            <div key={ip.id} className="c2-card overflow-hidden">
              <div
                className="px-4 py-3 flex items-center gap-4 cursor-pointer"
                onClick={() => setExpandedIp(expandedIp === ip.id ? null : ip.id)}
              >
                <span className="c2-pulse" />
                <span className="td-mono text-cyan text-[0.9rem] flex-1">{ip.address}</span>
                {ip.version && <span className="c2-badge c2-badge--muted">IPv{ip.version}</span>}
                <span className="c2-badge c2-badge--green">{ip.ports.length} PORT{ip.ports.length !== 1 ? 'S' : ''}</span>
                <span
                  className="text-text-muted text-[0.8rem] transition-transform duration-200 inline-block"
                  style={{ transform: expandedIp === ip.id ? 'rotate(90deg)' : 'none' }}
                >\u25B6</span>
              </div>
              {expandedIp === ip.id && ip.ports.length > 0 && (
                <div className="border-t border-border-subtle">
                  <table className="c2-table text-[0.75rem]">
                    <thead><tr>
                      <th>PORT</th><th>PROTOCOL</th><th>STATE</th><th>SERVICE</th><th>VERSION</th><th>FIRST SEEN</th>
                    </tr></thead>
                    <tbody>
                      {ip.ports.map(port => (
                        <tr key={port.id}>
                          <td className="td-mono text-amber">{port.port_number}</td>
                          <td className="td-mono">{port.protocol?.toUpperCase()}</td>
                          <td><StatusBadge status={port.state} /></td>
                          <td className="td-mono">{port.service_name || '\u2014'}</td>
                          <td className="td-muted">{port.service_version || '\u2014'}</td>
                          <td className="td-muted">{port.first_seen ? new Date(port.first_seen).toLocaleDateString() : '\u2014'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {expandedIp === ip.id && ip.ports.length === 0 && (
                <div className="px-4 py-3 text-text-muted font-mono text-[0.75rem] border-t border-border-subtle">
                  No open ports recorded. Run Nmap to scan.
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!tabLoading && ipTotalCount > pageSize && (
        <div className="flex justify-center gap-2 py-3">
          <button
            className="c2-btn c2-btn--ghost text-[0.75rem]"
            onClick={() => onFetch(ipPage - 1, ipSortBy, ipPortFilter)}
            disabled={ipPage === 0}
          >\u2190 PREVIOUS</button>
          <span className="text-[0.75rem] text-text-muted font-mono flex items-center">
            {ipPage * pageSize + 1} \u2014 {Math.min((ipPage + 1) * pageSize, ipTotalCount)} / {ipTotalCount}
          </span>
          <button
            className="c2-btn c2-btn--ghost text-[0.75rem]"
            onClick={() => onFetch(ipPage + 1, ipSortBy, ipPortFilter)}
            disabled={(ipPage + 1) * pageSize >= ipTotalCount}
          >NEXT \u2192</button>
        </div>
      )}
    </>
  );
};

export default IPsTabContent;
