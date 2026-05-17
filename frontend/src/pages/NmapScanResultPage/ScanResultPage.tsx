// 檔案路徑: frontend/src/pages/ScanResultPage/ScanResultPage.tsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom'; // 導入 useParams 獲取 URL 參數
import axios from 'axios';
// 導入你的類型定義。操！注意路徑！它在 src/pages/ 下面，所以是 ../../type
import type { NmapScanSchema, PortSchema } from '../../type'; 
import './ScanResultPage.css'; // 導入專屬的 CSS

// 操！你的後端 API 基本路徑！
const API_BASE_URL_NMAP = 'http://127.0.0.1:8000/api/nmap'; 

function ScanResultPage() {
  // 從 URL 裡同時獲取 targetId 和 scanId 參數！
  const { targetId, scanId } = useParams<{ targetId: string; scanId: string }>(); // <--- 就是這裡！
  
  // 狀態：儲存掃描結果，載入狀態，和錯誤訊息
  const [scanResult, setScanResult] = useState<NmapScanSchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScanResult = async () => {
      setLoading(true); 
      setError(null);   
      try {
        // 呼叫後端 API 獲取單個掃描詳情，仍然只用 scanId
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

    // 確保 targetId 和 scanId 都存在才執行數據獲取
    if (targetId && scanId) { 
      fetchScanResult();
    }
  }, [targetId, scanId]); // 依賴於 targetId 和 scanId，當任何一個變化時重新執行

  // 渲染載入狀態
  if (loading) {
    return (
      <div className="scan-result-container">
        <h1>掃描結果載入中...</h1>
        <p>正在為目標 ID: {targetId} 載入掃描任務 ID: {scanId} 的詳情...</p>
      </div>
    );
  }

  // 渲染錯誤狀態
  if (error) {
    return (
      <div className="scan-result-container">
        <h1 className="error-title">操！載入失敗！</h1>
        <p className="error-message">{error}</p>
        <p>請檢查掃描任務 ID 或目標 ID 是否正確，或後端服務是否正常。</p>
      </div>
    );
  }

  // 如果沒有掃描結果
  if (!scanResult) {
    return (
      <div className="scan-result-container">
        <h1>未找到掃描結果。</h1>
        <p>可能該掃描任務不存在或已刪除。</p>
      </div>
    );
  }

  // 渲染掃描結果
  return (
    <div className="scan-result-container">
      <h1>掃描報告: {scanResult.target_id} - {scanResult.scan_type}</h1>
      <p><strong>掃描任務 ID:</strong> {scanResult.id}</p>
      <p><strong>目標 ID:</strong> {scanResult.target_id}</p> {/* 顯示後端回傳的 target_id */}
      <p><strong>掃描類型:</strong> {scanResult.scan_type}</p>
      <p><strong>狀態:</strong> <span className={`status-${scanResult.status.toLowerCase()}`}>{scanResult.status}</span></p>
      <p><strong>開始時間:</strong> {new Date(scanResult.started_at).toLocaleString()}</p>
      {scanResult.completed_at && <p><strong>完成時間:</strong> {new Date(scanResult.completed_at).toLocaleString()}</p>}
      {scanResult.error_message && <p className="error-message"><strong>錯誤信息:</strong> {scanResult.error_message}</p>}

      <h2>掃描到的埠 ({scanResult.ports.length} 個)</h2>
      {scanResult.ports.length === 0 ? (
        <p>沒有掃描到開放埠。</p>
      ) : (
        <div className="port-list">
          {scanResult.ports.map((port: PortSchema) => (
            <div key={`${port.port_number}-${port.protocol}`} className="port-item">
              <p><strong>埠號:</strong> {port.port_number}/{port.protocol}</p>
              <p><strong>狀態:</strong> <span className={`port-state-${port.state.toLowerCase()}`}>{port.state}</span></p>
              {port.service_name && <p><strong>服務:</strong> {port.service_name}</p>}
              {port.service_version && <p><strong>版本:</strong> {port.service_version}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ScanResultPage;
