C2 Django AI - 系統架構與領域知識 (Project Knowledge)
這份文件總結了 C2 Django AI 專案的核心架構知識，特別聚焦於 AI 智能體架構 (3-Tier Agent Architecture) 以及 前端設計 (Cyberpunk UI & GraphQL Integration)。

1. 核心 AI 架構 (3-Tier Agent Architecture)
   系統採用三層式智能體分層設計，透過顯式呼叫 (Tool Invocation) 與隱式數據庫共享 (Database Context) 達到高度自動化的滲透測試循環。

Layer 1: 使用者溝通層 (User-Facing)
核心代理:

PersonalManagerAgent
職責: 直接與使用者互動的自然語言入口。負責理解高階需求（例如：「幫我掃描 Google 的子域名」），並將任務下達給 Layer 2。
實作方式: 透過 django_ai_assistant 定義，擁有呼叫 Layer 2 (HackerAssistantAgent) 作為工具 (Tool) 的能力。
Layer 2: 總指揮層 (Orchestrator)
核心代理:

HackerAssistantAgent
職責: 負責戰略規劃與任務分發。它不負責具體的「打點」工作，而是讀取資料庫中的

Overview
(目標專案概覽)，決定策略後調派 Layer 3。
具備 Tool/權限:

get_target_overview
: 讀取目標當前的知識庫與計畫。

create_or_update_target_overview
: 更新計畫與風險分數。

AutomationAgent
/

IPAnalyzerAgent
/

SubdomainAnalyzerAgent
: 呼叫第三層的工具。
Layer 3: 具體執行與分析層 (Executing & Analyzing Agents)
核心代理:

AutomationAgent
(整體 4-Phase 排程) 與各類專職 Analyzer。
職責: 執行實質命令與建立攻擊向量 (AttackVector)。
具備 Tool/權限:
動態生成的 OpenAPI Tools: (例如調用 Nmap, Subfinder, Nuclei API)。
資料庫更新 Tools:

create_step
(建立執行步驟與攻擊向量)、

create_verification
(設定驗證標準)。

get_exhausted_attack_vectors
: 獲取歷史失敗的攻擊向量，避免重複執行無效攻擊。
AI 智能體之間的協作與溝通機制 (Layer 2 & Layer 3)
Layer 2 (指揮官) 與 Layer 3 (執行者) 的協作機制分為兩條獨立且互補的通道：

顯式溝通 (Tool Invocation & Thread I/O)：
Layer 2 將 Layer 3 封裝為「Tool (工具)」。當 Layer 2 決定要發起攻擊時，會將戰略參數打包成文字 (Input) 呼叫該工具。
Layer 3 收到 Input 後，開啟內部的思考迴圈 (Thread) 並實際調用 OpenAPI 或資料庫 Tools。完成後，Layer 3 將執行摘要與總結作為返回值 (Output) 交還給 Layer 2 的工具對話層。
隱式溝通 (Shared Database Context)：
資料庫負責承載雙方的長短期記憶，避免 LLM 的 Token 上下文視窗被塞爆。
共用黑板：Layer 2 會以

create_or_update_target_overview
更新

Overview
的計畫與風險分數；Layer 3 啟動時首先會去閱讀

Overview
的狀態了解即將執行的策略方向。
進度追蹤：Layer 3 透過不斷建立

Step
與

AttackVector
把動作寫入資料庫，Layer 2 則能隨時呼叫

get_target_overview
檢查 Layer 3 的作戰進度是否順利，並決定是否要變更戰略。
第零層: 資料預處理與觸發 (Data Pre-processing Layer)
核心機制:

periodic_initial_analysis_bootstrapper
(Celery Beat 定時任務)。
運作邏輯:
定期掃描尚未被歸入 Overview 的新資產 (IP / Subdomain / URLResult)。
交由

InitialAnalyzerAgent
評估並產生

InitialAIAnalysis
記錄，打上 risk_score (0-100)。
自動叢集化 (Clustering): 若 risk_score >= 70，後端邏輯 (

process_initial_analysis_conversions
) 會自動為這批高風險資產建立一個新的

Overview
，從而喚醒 Layer 2 接手後續的自動化攻擊。
Watchdog 機制: 廢棄了舊版盲目重啟的 watchdog，改為單純將超時無回應的 Overview 標記為 STALLED 或 FAILED。2. 前端架構與設計 (Frontend Architecture & Design)
前端負責資料的即時呈現與系統控制，採用 Cyberpunk (駭客風) 的極致美學，並透過 Hasura GraphQL 即時聯動後端。

視覺設計準則 (Cyberpunk UI Aesthetics)
色彩系統:
主背景：深邃黑/深藍 (#09090b / #0a0a0a)。
點綴色 (Neon)：螢光綠 (#00ff00, #10B981) 作為成功/運行狀態、螢光黃 (#eab308) 警告、螢光紅 (#ef4444) 代表漏洞與失敗風險、螢光粉紅與電光藍作為標籤。
字型與排版:
大量使用等寬字體 (Monospace, e.g., Fira Code)，確保讀取數據、終端機輸出、程式碼時擁有對齊的冷峻科技感。
微動畫特效 (Micro-animations):
呼吸燈發光 (Glow effects)、Scanline (CRT 掃描線) 覆蓋、毛玻璃 (Glassmorphism)，使冰冷的數據呈現生命力，讓 Dashboard 變成指揮官儀表板。
核心介面 (Key Pages)
AI Center (

AICenterPage.tsx
):
包含可拖曳調整寬度的分割畫面 (Split Pane)。左側為與 Layer 1 AI 對話的 Chat Window（支持 Markdown 渲染），右側為即時分析執行結果。
目標總覽 (

TargetDashboard.tsx
):
展示掃描專案進度、風險評分趨勢與 Overview 執行狀態。
域名/URL 威脅情資頁 (

UrlDetailPage.tsx
&

SeedReconPage.tsx
):
透過可折疊面板 (Collapsible Sections) 排列龐雜的滲透資料（如 HTTP Status 徽章、Headers、Forms(parameters)、Links、MetaTags(attributes)、Vulnerabilities）。
避免畫面擁擠，針對不同的技術棧 (TechStack) 與弱點 (Vulnerability) 給予專屬顏色的標籤。
數據綁定 (GraphQL / Hasura)
使用 Apollo Client 結合 Vite。對應 Django ORM 中的多對多關聯，前端需注意 Hasura 自動生成的欄位名稱。
常見 Mapping 雷區歸納:
core_techstack → 使用 name, categories。(非 technology, category)
core_metatag → 使用 attributes (JSONField)。
core_form → 使用 parameters (而非 inputs_json)。
Query 需使用正確的外鍵查詢，例如從 Target

id
查所有關聯的 URL (core_urlresult(where: {subdomain: {seed: {target_id: {\_eq: $targetId}}}}) 等關聯路徑)。
