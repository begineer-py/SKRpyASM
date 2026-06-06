# Core App

`apps/core` 是整個系統的核心模型層，但目前對外公開 API 的範圍比文檔常描述的更小。

## 實際職責

- 持有系統主要模型
- 提供 `Step` 與 `Overview` 的對外 API
- 承載 assistant/thread/message、compression、analysis 等核心資料結構

## 模型層定位

`apps/core` 實際擁有的資料範圍包含：

- 資產模型：`Target`、`Seed`、`IP`、`Port`、`Subdomain`、`URLResult`
- 掃描記錄模型：Nmap/Subfinder/Amass/Nuclei 等 scan records
- 分析模型：`InitialAIAnalysis`、`Overview`、`Step`、`StepLog`、`AttackVector`
- assistant 相關模型：`Thread`、`Message`
- 壓縮相關模型：thread compression state 等
- CVE intelligence 相關模型

## 公開 API 現況

`c2_core/urls.py` 將 `apps/core` 掛在 `/api/core`，但目前實際公開 endpoint 主要來自兩個 router。

### Steps API

來源：`apps/core/step_api.py`

- `POST /api/core/steps/`
- `PATCH /api/core/steps/{step_id}`
- `DELETE /api/core/steps/{step_id}`
- `PUT /api/core/steps/{step_id}/note/`

### Overviews API

來源：`apps/core/overview_api.py`

- `GET /api/core/overviews/`
- `GET /api/core/overviews/{overview_id}`
- `POST /api/core/overviews/`
- `PATCH /api/core/overviews/{overview_id}`
- `DELETE /api/core/overviews/{overview_id}`

### 空 router

`apps/core/api.py` 目前只有空的 `Router()`，沒有額外 endpoint。

這代表：

- 文檔若把 `/api/core` 寫成廣泛的「核心資產模型 API」，會超過目前事實
- 更準確的說法是：
  - `apps/core` 是核心模型層
  - 對外 API 目前主要集中在 `Step` 和 `Overview`

## 與其他 app 的關係

- `apps/targets` 新增 seed 時會建立 core asset records
- `apps/scanners` 與 `apps/flaresolverr` 會把掃描結果寫回 core models
- `apps/analyze_ai` 會建立 `InitialAIAnalysis` 與 `Overview`
- `apps/auto` 以 `Overview`、`Step`、`Thread` 為核心執行自動化
- `apps/ai_assistant` 雖然有自己的 app，但實際 thread/message 模型已在 `core`

## 文檔注意事項

- 對外文檔應避免把 `core` 與「公開 API 範圍」混為一談
- 若要介紹 `core`，應分開寫：
  - 模型責任
  - 對外 API

## 相關檔案

- `apps/core/models/__init__.py`
- `apps/core/api.py`
- `apps/core/step_api.py`
- `apps/core/overview_api.py`

---

_最后更新：2026-06-06_
