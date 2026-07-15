// 檔案路徑: frontend/src/pages/ScanResultPage/ScanResultPage.tsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import type { NmapScanSchema, PortSchema } from '../../../type';
import { cn } from '@/lib/utils';

const API_BASE_URL_NMAP = 'http://127.0.0.1:8000/api/nmap';

const statusColors: Record<string, string> = {
  pending: 'c2-badge c2-badge--amber', completed: 'c2-badge c2-badge--green',
  failed: 'c2-badge c2-badge--red', running: 'c2-badge c2-badge--cyan',
};

const portStateColors: Record<string, string> = {
  open: 'text-green font-semibold', closed: 'text-red font-semibold', filtered: 'text-amber font-semibold',
};

function ScanResultPage() {
  const { targetId, scanId } = useParams<{ targetId: string; scanId: string }>();

  const [scanResult, setScanResult] = useState<NmapScanSchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScanResult = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get<NmapScanSchema>(`${API_BASE_URL_NMAP}/get_scan/${scanId}`);
        setScanResult(response.data);
      } catch (err: unknown) {
        console.error('媽的！獲取掃描結果失敗:', err);
        const response = (err as { response?: { data?: { message?: string } } }).response;
        if (response?.data?.message) {
          setError(`錯誤: ${response.data.message}`);
        } else {
          setError('操！無法獲取掃描結果，請檢查網絡或服務器！');
        }
      } finally {
        setLoading(false);
      }
    };

    if (targetId && scanId) {
      fetchScanResult();
      return;
    }
    setError('缺少掃描任務識別碼，無法載入結果。');
    setLoading(false);
  }, [targetId, scanId]);

  const containerCls = 'c2-page max-w-[1400px]';
  const panelCls = 'c2-card p-5';

  if (loading) {
    return (
      <div className={containerCls}><div className={panelCls}>
        <div className="c2-loading">正在載入掃描結果…</div>
      </div></div>
    );
  }

  if (error) {
    return (
      <div className={containerCls}><div className="rounded-2xl border border-red/30 bg-red/10 p-5">
        <h1 className="text-xl font-semibold text-text-primary">無法載入掃描結果</h1>
        <p className="mt-3 text-sm text-red">{error}</p>
        <p className="mt-3 text-sm text-text-secondary">請確認目標與掃描任務識別碼，或檢查後端服務狀態。</p>
      </div></div>
    );
  }

  if (!scanResult) {
    return (
      <div className={containerCls}><div className="c2-empty">
        找不到掃描結果。此任務可能已刪除，或尚未完成寫入。
      </div></div>
    );
  }

  return (
    <div className={containerCls}>
      <section className={panelCls}>
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border-subtle pb-5">
          <div><h1 className="text-2xl font-semibold text-text-primary">Nmap 掃描結果</h1><p className="mt-2 text-sm text-text-secondary">目標 #{scanResult.target_id} · {scanResult.scan_type}</p></div>
          <span className={cn(statusColors[scanResult.status.toLowerCase()] || 'c2-badge c2-badge--muted')}>{scanResult.status}</span>
        </div>
        <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-xs font-mono text-text-muted">掃描 ID</dt><dd className="mt-1 font-mono text-sm text-text-primary">{scanResult.id}</dd></div>
          <div><dt className="text-xs font-mono text-text-muted">目標 ID</dt><dd className="mt-1 font-mono text-sm text-text-primary">{scanResult.target_id}</dd></div>
          <div><dt className="text-xs font-mono text-text-muted">開始時間</dt><dd className="mt-1 text-sm text-text-primary">{new Date(scanResult.started_at).toLocaleString()}</dd></div>
          {scanResult.completed_at && <div><dt className="text-xs font-mono text-text-muted">完成時間</dt><dd className="mt-1 text-sm text-text-primary">{new Date(scanResult.completed_at).toLocaleString()}</dd></div>}
        </dl>
        {scanResult.error_message && <p className="mt-5 rounded-xl border border-red/30 bg-red/10 p-4 text-sm text-red"><strong>掃描錯誤：</strong>{scanResult.error_message}</p>}
      </section>

      <section className={`${panelCls} mt-6`}>
        <div className="mb-5 border-b border-border-subtle pb-4"><h2 className="text-lg font-semibold text-text-primary">發現的埠</h2><p className="mt-1 text-sm text-text-secondary">共 {scanResult.ports.length} 個服務端點</p></div>
      {scanResult.ports.length === 0 ? (
        <div className="c2-empty">這次掃描沒有發現開放埠。</div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4">
          {scanResult.ports.map((port: PortSchema) => (
            <div key={`${port.port_number}-${port.protocol}`} className="rounded-xl border border-border-subtle bg-bg-panel p-4 transition-colors hover:border-border-normal hover:bg-bg-card-hover">
              <p className="font-mono text-lg font-semibold text-text-primary">{port.port_number}<span className="text-text-muted">/{port.protocol}</span></p>
              <p className="mt-3 text-sm text-text-secondary">狀態：<span className={cn(portStateColors[port.state.toLowerCase()] || 'font-semibold')}>{port.state}</span></p>
              {port.service_name && <p className="mt-2 text-sm text-text-secondary">服務：<span className="text-text-primary">{port.service_name}</span></p>}
              {port.service_version && <p className="mt-2 text-sm text-text-secondary">版本：<span className="text-text-primary">{port.service_version}</span></p>}
            </div>
          ))}
        </div>
      )}
      </section>
    </div>
  );
}

export default ScanResultPage;
