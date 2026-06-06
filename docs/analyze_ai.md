# Analyze AI App

`apps/analyze_ai` 是目前 AI 初步分析與策略規劃的中介層。它不是廣泛的公開 AI API 平台，而是把資產轉為 `Overview` 與規劃流程的關鍵橋樑。

## 實際職責

- 為新資產建立 `InitialAIAnalysis`
- 執行初步 AI 分析 batch
- 把高價值分析結果轉為 `Overview`
- 以 `Overview` 為中心產生下一步計畫
- 規劃完成後鏈式觸發 `apps.auto`

## 公開 API 現況

目前公開 API 很小，只有：

- `POST /api/analyze_ai/initial`

來源：`apps/analyze_ai/api.py`

## 目前流程

### 1. 初步分析建立

`apps/analyze_ai/tasks/initial_tasks.py`

- `trigger_initial_ai_analysis`
  - 根據 `ip_ids`、`subdomain_ids`、`url_ids` 建立 `InitialAIAnalysis` 記錄
- `perform_initial_ai_analysis_batch`
  - 執行 batch 分析
- `process_initial_analysis_conversions`
  - 將 `worth_deep_analysis=True` 的結果轉為或附加到 `Overview`

### 2. 週期性引導

- `periodic_initial_analysis_bootstrapper`
  - 找出值得分析的新 IP / Subdomain / URL
  - 自動派發初步分析

### 3. 規劃

`apps/analyze_ai/tasks/planning.py`

- `propose_next_steps(overview_id)`
  - 讀取 `Overview` 的資產、歷史 step、attack vectors
  - 產生 `plan`
  - 建立新的 `Step`
  - 規劃成功後鏈式觸發 `auto_execute_plan`

## 與其他 app 的關係

- 依賴 `apps/core` 的 `InitialAIAnalysis`、`Overview`、`Step`
- 規劃完成後呼叫 `apps.auto.tasks.auto_execute_plan`
- 由 scheduler 可定期觸發分析與規劃相關流程

## 已知實作注意點

### API / task 參數不一致

目前 `apps/analyze_ai/api.py` 會這樣派發：

- `trigger_initial_ai_analysis.delay(analysis_ids=valid_ids)`

但實際 task 定義是：

- `trigger_initial_ai_analysis(ip_ids=None, subdomain_ids=None, url_ids=None, overview_id=None)`

這表示目前 API 與 task 介面存在不一致，文檔若描述此端點時需要標註這點，或直接以程式修正為準。

## 文檔注意事項

- 不要把 `apps/analyze_ai` 寫成成熟的多端點 AI 公開 API
- 目前更準確的定位是：
  - 初步分析入口
  - `Overview` 建立與策略規劃中樞

## 相關檔案

- `apps/analyze_ai/api.py`
- `apps/analyze_ai/tasks/initial_tasks.py`
- `apps/analyze_ai/tasks/planning.py`
- `apps/analyze_ai/assistants.py`

---

_最后更新：2026-06-06_
