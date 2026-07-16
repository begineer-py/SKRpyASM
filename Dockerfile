FROM python:3.10-slim

# Build arguments for tool versions (reproducible builds)
ARG SUBFINDER_VERSION=2.6.6
ARG NUCLEI_VERSION=3.1.0
ARG KATANA_VERSION=1.1.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Prevent writing .pyc files and ensure unbuffered output
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 系統依賴：nmap（python-nmap 呼叫系統二進位）、wget/unzip（下載 Go 工具）
# NOTE: docker-cli 與 nodejs 理論上應在此安裝（httpx 呼叫與 JS endpoint 抽取需要），
# 但本部署環境氣隙，build 時無外網。改為：
#   - js_parser 已改為 Node.js 缺失時優雅降級（不影響 scan 主流程）
#   - httpx 失敗時 MySpider 會 fallback 到 FlareSolverr（HTTP API，不需 docker CLI）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmagic1 \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install security tools with pinned versions via ARGs
# subfinder
RUN wget -qO /tmp/sf.zip \
    https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.zip \
    && unzip -q /tmp/sf.zip subfinder -d /usr/local/bin \
    && chmod +x /usr/local/bin/subfinder \
    && rm /tmp/sf.zip \
    && subfinder -version

# nuclei
RUN wget -qO /tmp/nu.zip \
    https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip \
    && unzip -q /tmp/nu.zip nuclei -d /usr/local/bin \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nu.zip \
    && nuclei -version

# katana
RUN wget -qO /tmp/kt.zip \
    https://github.com/projectdiscovery/katana/releases/download/v${KATANA_VERSION}/katana_${KATANA_VERSION}_linux_amd64.zip \
    && unzip -q /tmp/kt.zip katana -d /usr/local/bin \
    && chmod +x /usr/local/bin/katana \
    && rm /tmp/kt.zip \
    && katana -version

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code (this layer changes frequently, so put it after requirements)
COPY . .

# 建立日誌目錄（對應 settings.py LOG_DIR）
RUN mkdir -p /app/c2_core/logs

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app /usr/local/bin/subfinder /usr/local/bin/nuclei /usr/local/bin/katana \
    && chmod 777 /app/c2_core/logs

# Switch to non-root user
USER appuser

EXPOSE 8000

# 默認：uvicorn web server
# docker-compose 中 celery 服務會覆蓋此 CMD
CMD ["uvicorn", "c2_core.asgi:application", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools"]
