# C2 Django AI - 隨身碟便攜包

## 內容物

| 檔案 | 大小 | 說明 |
|---|---|---|
| `c2-source.tar.gz` | ~689 MB | 完整原始碼 + .git 歷史 + ML 推論模型 |
| `c2-all-images.tar` | ~9.9 GB | 11 個 Docker image（離線部署用） |
| `config/.env` | 2 KB | 後端環境變數（含 API Key） |
| `config/frontend.env` | 0.5 KB | 前端環境變數 |
| `quick-setup-local.sh` | 12 KB | 一鍵部署腳本 |

## 在新筆電上還原

### 1. 前置需求
- Docker + Docker Compose
- Python 3.10+（僅前端開發模式需要 Node.js 18+）

### 2. 還原步驟

```bash
# (1) 解壓原始碼到目標位置
mkdir -p ~/Desktop/share/C2_Django_AI_git
cd ~/Desktop/share/C2_Django_AI_git
tar xzf /media/$USER/6A46-9443/C2_Django_AI_portable/c2-source.tar.gz

# (2) 複製設定檔
cp /media/$USER/6A46-9443/C2_Django_AI_portable/config/.env .env
cp /media/$USER/6A46-9443/C2_Django_AI_portable/config/frontend.env frontend/.env
cp /media/$USER/6A46-9443/C2_Django_AI_portable/quick-setup-local.sh .

# (3) 建立 docker-images 目錄並複製 image tar
mkdir -p docker-images
cp /media/$USER/6A46-9443/C2_Django_AI_portable/c2-all-images.tar docker-images/

# (4) 一鍵啟動（載入 image + 生成 .env + docker compose up）
./quick-setup-local.sh
```

### 3. 一行版（懶人包）

```bash
mkdir -p ~/Desktop/share/C2_Django_AI_git && \
cd ~/Desktop/share/C2_Django_AI_git && \
USB=/media/$USER/6A46-9443/C2_Django_AI_portable && \
tar xzf $USB/c2-source.tar.gz && \
cp $USB/config/.env .env && \
cp $USB/config/frontend.env frontend/.env && \
cp $USB/quick-setup-local.sh . && \
mkdir -p docker-images && cp $USB/c2-all-images.tar docker-images/ && \
./quick-setup-local.sh
```

## 服務入口（啟動後）

| 服務 | URL |
|---|---|
| Frontend (nginx) | http://127.0.0.1 |
| Django API | http://127.0.0.1:8000/api |
| Django Admin | http://127.0.0.1:8000/admin/ |
| Hasura Console | http://127.0.0.1:8085 |
| NocoDB | http://127.0.0.1:8081 |
| FlareSolverr | http://127.0.0.1:8191 |

## 注意事項

- **API Key 已寫入 .env**，包括 OpenAI (yuhuanstudio provider) — 請妥善保管隨身碟
- **ML 推論模型**（4 個 model.safetensors，共 ~348 MB）已打包在 c2-source.tar.gz 內
- **訓練 checkpoint**（1.56 GB）已排除，僅保留最終推論模型
- **node_modules / __pycache__ / .venv** 已排除，在新機器上重新生成即可
- Docker image 包含 `c2_kali_sandbox`（6.7 GB），佔整個 image tar 的 2/3
