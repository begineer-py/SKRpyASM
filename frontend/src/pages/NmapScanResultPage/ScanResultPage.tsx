// 檔案路徑: frontend/src/pages/ScanResultPage/ScanResultPage.tsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import type { NmapScanSchema, PortSchema } from '../../type';
import { cn } from '@/lib/utils';

const API_BASE_URL_NMAP = 'http://127.0.0.1:8000/api/nmap';

const statusColors: Record<string, string> = {
  pending: 'text-yellow-300 font-bold',
  completed: 'text-[#00ff00] font-bold',
  failed: 'text-red-500 font-bold',
  running: 'text-cyan-400 font-bold',
};

const portStateColors: Record<string, string> = {
  open: 'text-[#00ff00] font-bold',
  closed: 'text-red-500 font-bold',
  filtered: 'text-yellow-300 font-bold',
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
      } catch (err: any) {
        console.error('媽的！獲取掃描結果失敗:', err);
        if (err.response && err.response.data && err.response.data.message) {
          setError(`錯誤: ${err.response.data.message}`);
        } else {
          setError('操！無法獲取掃描結果，請檢查網絡或服務器！');
        }
      } finally {
        setLoading(false);
      }
    };

    if (targetId && scanId) {
      fetchScanResult();
    }
  }, [targetId, scanId]);

  const containerCls = "max-w-4xl mx-auto my-10 p-8 bg-[#0a0a0a] border border-[#00ff00] rounded shadow-[0_0_20px_rgba(0,255,0,0.5)] text-[#00ff00] font-mono max-md:my-5 max-md:p-5";
  const h1Cls = "text-[#00ff00] text-center mb-8 text-[2.8em] [text-shadow:0_0_10px_rgba(0,255,0,0.7)] border-b-2 border-dashed border-[#008800] pb-4 max-md:text-[2em]";
  const h2Cls = "text-[#00ff00] mt-10 mb-5 text-[2em] [text-shadow:0_0_8px_rgba(0,255,0,0.5)] border-b border-dashed border-[#008800] pb-2.5 max-md:text-[1.5em]";
  const pCls = "mb-2.5 leading-relaxed text-[1.1em]";

  if (loading) {
    return (
      <div className={containerCls}>
        <h1 className={h1Cls}>掃描結果載入中...</h1>
        <p className={pCls}>正在為目標 ID: {targetId} 載入掃描任務 ID: {scanId} 的詳情...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={containerCls}>
        <h1 className="text-red-500 text-center text-[2.5em] [text-shadow:0_0_10px_rgba(255,0,0,0.7)]">操！載入失敗！</h1>
        <p className="text-red-500 font-bold bg-[#330000] p-4 rounded-lg border border-red-500 mt-5 shadow-[0_0_10px_rgba(255,0,0,0.5)]">{error}</p>
        <p className={pCls}>請檢查掃描任務 ID 或目標 ID 是否正確，或後端服務是否正常。</p>
      </div>
    );
  }

  if (!scanResult) {
    return (
      <div className={containerCls}>
        <h1 className={h1Cls}>未找到掃描結果。</h1>
        <p className={pCls}>可能該掃描任務不存在或已刪除。</p>
      </div>
    );
  }

  return (
    <div className={containerCls}>
      <h1 className={h1Cls}>掃描報告: {scanResult.target_id} - {scanResult.scan_type}</h1>
      <p className={pCls}><strong className="text-[#00ffff]">掃描任務 ID:</strong> {scanResult.id}</p>
      <p className={pCls}><strong className="text-[#00ffff]">目標 ID:</strong> {scanResult.target_id}</p>
      <p className={pCls}><strong className="text-[#00ffff]">掃描類型:</strong> {scanResult.scan_type}</p>
      <p className={pCls}><strong className="text-[#00ffff]">狀態:</strong> <span className={cn(statusColors[scanResult.status.toLowerCase()] || 'font-bold')}>{scanResult.status}</span></p>
      <p className={pCls}><strong className="text-[#00ffff]">開始時間:</strong> {new Date(scanResult.started_at).toLocaleString()}</p>
      {scanResult.completed_at && <p className={pCls}><strong className="text-[#00ffff]">完成時間:</strong> {new Date(scanResult.completed_at).toLocaleString()}</p>}
      {scanResult.error_message && <p className="text-red-500 font-bold bg-[#330000] p-4 rounded-lg border border-red-500 mt-5 shadow-[0_0_10px_rgba(255,0,0,0.5)]"><strong>錯誤信息:</strong> {scanResult.error_message}</p>}

      <h2 className={h2Cls}>掃描到的埠 ({scanResult.ports.length} 個)</h2>
      {scanResult.ports.length === 0 ? (
        <p className={pCls}>沒有掃描到開放埠。</p>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 mt-5 max-md:grid-cols-1">
          {scanResult.ports.map((port: PortSchema) => (
            <div key={`${port.port_number}-${port.protocol}`} className="bg-[#111111] border border-[#008800] rounded p-5 shadow-[0_0_10px_rgba(0,255,0,0.3)] transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_0_25px_rgba(0,255,0,0.7)]">
              <p className="mb-1 text-base"><strong className="text-[#00ffff]">埠號:</strong> {port.port_number}/{port.protocol}</p>
              <p className="mb-1 text-base"><strong className="text-[#00ffff]">狀態:</strong> <span className={cn(portStateColors[port.state.toLowerCase()] || 'font-bold')}>{port.state}</span></p>
              {port.service_name && <p className="mb-1 text-base"><strong className="text-[#00ffff]">服務:</strong> {port.service_name}</p>}
              {port.service_version && <p className="mb-1 text-base"><strong className="text-[#00ffff]">版本:</strong> {port.service_version}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ScanResultPage;
