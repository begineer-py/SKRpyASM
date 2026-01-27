# ⚠️ LEGAL DISCLAIMER

**FOR EDUCATIONAL AND ETHICAL TESTING PURPOSES ONLY**

Usage of C2 Django AI for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws.

## 中文免責聲明
本工具僅限於「受控環境下的安全研究」與「獲得明確書面授權的滲透測試」。未經授權的掃描與滲透可能違反相關網路安全法律。開發者對於使用者之任何違法行為不負任何連帶責任。

**By using this software, you agree that you are solely responsible for your own actions. The software is provided "as is", without warranty of any kind, express or implied.**
# C2 Django AI - 全方位網路安全掃描平台

## 項目概述

C2 Django AI是一個全方位的網路安全掃描和滲透測試平台，集成了現代化的AI分析能力。該系統採用Django後端框架，結合React前端界面，提供從資產發現、端口掃描到深度AI分析的完整工作流程。

## 架構總覽

### 核心技術棧
- **後端框架**: Django 5.2.9 + Django REST Framework
- **數據庫**: PostgreSQL (通過Docker容器運行)
- **任務隊列**: Redis + Celery
- **前端**: React 18 + TypeScript + Vite
- **容器化**: Docker Compose
- **API代理**: 自定義代理服務支持多個AI API (Gemini, Mistral等)

## 🚀 Key Features

### 🔍 **Comprehensive Asset Discovery**
- **Subdomain Enumeration**: Multi-source subdomain discovery with Subfinder
- **Port Scanning**: Advanced Nmap integration with service detection
- **URL Discovery**: Deep web crawling and endpoint mapping
- **Technology Stack**: Automatic detection with Wappalyzer and custom scanners

### 🤖 **AI-Powered Analysis**
- **Risk Assessment**: AI-driven vulnerability and security analysis
- **Business Intelligence**: Automated importance classification of assets
- **Content Analysis**: Sensitive information extraction and classification
- **Multi-Provider Support**: Gemini, Mistral, and custom AI services

### 🛡️ **Advanced Scanning Tools**
- **Nmap Scanner**: Asynchronous port scanning with detailed service analysis
- **Nuclei Integration**: Template-based vulnerability scanning
- **WAF Detection**: Automatic firewall and CDN identification
- **Anti-Bot Bypass**: FlareSolverr integration for protected sites

### 📊 **Management & Visualization**
- **Django Admin**: Comprehensive asset and scan management
- **GraphQL API**: Hasura-powered complex data queries
- **NocoDB Interface**: Excel-like data exploration
- **React Dashboard**: Modern, responsive frontend with TypeScript

## 🏗️ Architecture Overview

### Core Technology Stack
- **Backend**: Django 5.2.9 + Django REST Framework + Django Ninja
- **Database**: PostgreSQL (Dockerized)
- **Queue System**: Redis + Celery with Eventlet
- **Frontend**: React 18 + TypeScript + Vite
- **API Layer**: Hasura GraphQL Engine
- **Containerization**: Docker Compose

### External Dependencies
- **Security Tools**: Nmap, Subfinder, Nuclei, dnsx, cdncheck
- **AI Services**: Gemini, Mistral, Custom Proxy Services
- **Anti-Bot**: FlareSolverr + Proxy Management
- **Admin Interface**: NocoDB for data management

## 🚀 Quick Start

### Prerequisites
- **OS**: Ubuntu 22.04+ or equivalent
- **Hardware**: 2+ vCPU, 4GB+ RAM
- **Software**: Docker, Docker Compose, Conda/Miniconda

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/begineer-py/MTC-Master-tools-combination-.git
cd MTC-Master-tools-combination-

# 2. Start infrastructure services
docker compose up -d

# 3. Setup Python environment
conda create -n mtc_env python=3.10 -y
conda activate mtc_env
pip install -r requirements.txt

# 4. Initialize database
python manage.py migrate
python manage.py createsuperuser

# 5. Start services
# Terminal 1: Django
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Worker
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info

# Terminal 3: Celery Beat
celery -A c2_core beat -l info
```

### Access Points
- **Main API**: http://127.0.0.1:8000
- **Admin Panel**: http://127.0.0.1:8000/admin
- **GraphQL Console**: http://127.0.0.1:8085
- **Data Manager**: http://127.0.0.1:8081

📖 **For detailed installation and configuration, see [BUILD_GUIDE.md](BUILD_GUIDE.md)**

## 🛠️ Development

### Project Structure
```
├── core/                 # Core data models and business logic
├── analyze_ai/          # AI analysis integration
├── nmap_scanner/        # Nmap scanning module
├── subfinder/           # Subdomain discovery
├── flaresolverr/        # Web crawling and anti-bot
├── frontend/            # React frontend application
├── docker/              # Infrastructure configuration
└── scripts/             # Utility scripts
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Security Notice

This tool is designed for authorized security testing only. Users must ensure they have proper authorization before scanning any targets. The developers assume no liability for misuse.
