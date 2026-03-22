# ⚠️ LEGAL DISCLAIMER

**FOR EDUCATIONAL AND ETHICAL TESTING PURPOSES ONLY**

Usage of C2 Django AI for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws.

## 中文免責聲明

本工具僅限於「受控環境下的安全研究」與「獲得明確書面授權的滲透測試」。未經授權的掃描與滲透可能違反相關網路安全法律。開發者對於使用者之任何違法行為不負任何連帶責任。

**By using this software, you agree that you are solely responsible for your own actions. The software is provided "as is", without warranty of any kind, express or implied.**

# C2 Django AI - 全方位網路安全掃描平台

## 項目概述

C2 Django AI 是一個全方位的網路安全掃描和滲透測試平台，集成了現代化的 AI 分析能力。該系統採用 Django 後端框架，結合 React 前端界面，提供從資產發現、端口掃描到深度 AI 分析的完整工作流程。

## 🚀 核心功能

### 🔍 資產發現與偵察

- **子域名枚舉**: 集成 Subfinder 與 Amass，支持多來源子域名發現。
- **端口掃描**: 進階 Nmap 集成，支持異步服務識別與操作系統偵測。
- **URL 爬取**: 深度網頁爬取與端點映射。
- **技術棧識別**: 自動檢測目標應用的 Web 技術與框架。

### 🤖 AI 驅動分析

- **Initial AI Analysis**: 快速資產識別與初步風險點定位，優化資源分配。
- **Deep Attack Planning**: 基於資產發現結果生成深度攻擊計畫與步驟。
- **Continuous Overview**: 自動化執行的持續監控與決策環節。
- **多模型支持**: 支持 Gemini, Mistral 等主流 AI 模型。

### 🛡️ 進階安全工具

- **Nuclei 集成**: 基於模板的漏洞掃描。
- **WAF/CDN 偵測**: 自動化防火牆與內容分發網絡識別。
- **反爬蟲繞過**: 集成 FlareSolverr 處理受保護站點。

## 🏗️ 技術架構

- **後端**: Django 5.2.x + Django REST Framework + Django Ninja
- **任務調度**: Celery + Redis + Flower (任務監控)
- **數據庫**: PostgreSQL (主要存儲)
- **AI 引擎**: 自研 AI 分析調度邏輯，支持異步步驟回傳與動態計畫生成。
- **前端**: React 18 + TypeScript + Vite
- **基礎設施**: Docker Compose 容器化部署
- **API 層**: Hasura GraphQL 引擎 (複雜數據查詢)

## 🚀 快速啟動

### 前置要求

- **操作系統**: Ubuntu 22.04+ 或同等版本
- **軟體**: Docker, Docker Compose, Conda/Miniconda

### 安裝步驟

```bash
# 1. 克隆倉庫
git clone https://github.com/begineer-py/MTC-Master-tools-combination-.git
cd MTC-Master-tools-combination-

# 2. 啟動基礎設施
docker compose up -d

# 3. 設置 Python 環境
conda create -n mtc_env python=3.10 -y
conda activate mtc_env
pip install -r requirements.txt

# 4. 初始化數據庫
python manage.py migrate
python manage.py createsuperuser

# 5. 啟動服務
# Terminal 1: Django API
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Worker
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info
```

📖 **詳細安裝與配置指南請參閱 [BUILD_GUIDE.md](BUILD_GUIDE.md)**

## ⚠️ 免責聲明

**本工具僅限於「教育用途」與「授權的安全測試」。**
未經授權的掃描與滲透行為可能違法。使用者應對其行為負完全法律責任。
