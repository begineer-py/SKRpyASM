# 📚 C2 Django AI - Complete Build & Deployment Guide

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [System Requirements](#system-requirements)
3. [Prerequisites Installation](#prerequisites-installation)
4. [Quick Start (One-Command Setup)](#quick-start-one-command-setup)
5. [Detailed Installation](#detailed-installation)
6. [Configuration & Security](#configuration--security)
7. [Verification & Testing](#verification--testing)
8. [Operations & Maintenance](#operations--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)
11. [Security Hardening](#security-hardening)

---

## Overview & Architecture

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Django Backend  │    │  Celery Workers  │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Async Tasks)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Infrastructure                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ PostgreSQL  │ │    Redis    │ │   Hasura    │ │   NocoDB    │ │
│  │  (5432)     │ │   (6379)    │ │   (8085)    │ │   (8081)    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│  │FlareSolverr │ │FlareProxyGo │ │  NyaProxy   │                 │
│  │  (8191)     │ │  (8192)     │ │  (8502)     │                 │
│  └─────────────┘ └─────────────┘ └─────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Tools                               │
│  Nmap, Subfinder, Nuclei, dnsx, cdncheck, wafw00f               │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Django Backend (c2_core)

- **API Server**: RESTful endpoints and business logic
- **Authentication**: User management and access control
- **Task Orchestration**: Celery task scheduling and monitoring
- **Data Models**: Asset management and scan results

#### Celery Workers

- **Async Processing**: Background scanning tasks
- **Tool Integration**: External security tool execution
- **Error Handling**: Retry mechanisms and failure recovery
- **Result Processing**: Parse and store scan results

#### Infrastructure Services

- **PostgreSQL**: Primary data storage
- **Redis**: Task queue and caching
- **Hasura**: GraphQL API layer for complex queries
- **NocoDB**: Spreadsheet-like data management interface

#### External Tools

- **Nmap**: Port scanning and service detection
- **Subfinder**: Subdomain enumeration
- **Nuclei**: Vulnerability scanning with templates
- **FlareSolverr**: Anti-bot protection bypass

---

## System Requirements

### Minimum Requirements

- **CPU**: 2 vCPU
- **RAM**: 4GB
- **Storage**: 20GB free space
- **OS**: Ubuntu 22.04+ (recommended)

### Recommended Requirements

- **CPU**: 4+ vCPU
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection for AI services

### Supported Operating Systems

- Ubuntu 22.04+ (primary)
- Debian 11+
- CentOS 8+
- macOS 12+ (with limitations)
- Windows 10+ (WSL2 required)

---

## Prerequisites Installation

### 1. Docker & Docker Compose

#### Ubuntu/Debian

```bash
# Update package index
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Conda/Miniconda

#### Linux

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# Initialize conda
~/miniconda3/bin/conda init bash
source ~/.bashrc

# Verify installation
conda --version
```

#### macOS

```bash
# Download Miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-MacOSX-x86_64.sh -b -p $HOME/miniconda3

# Initialize conda
~/miniconda3/bin/conda init zsh
source ~/.zshrc
```

### 3. System Dependencies

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libmagic1 \
    libmagic-dev \
    nmap \
    git \
    curl \
    wget \
    golang-go
```

#### CentOS/RHEL

```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    python3-devel \
    openssl-devel \
    libffi-devel \
    libxml2-devel \
    libxslt-devel \
    zlib-devel \
    libjpeg-turbo-devel \
    libpng-devel \
    file-devel \
    nmap \
    git \
    curl \
    wget \
    golang
```

### 4. Go Tools Installation

```bash
# Set up Go environment
export PATH=$PATH:~/go/bin
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc

# Install Project Discovery tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

# Install other security tools
go install -v github.com/Edu4rdSHL/wafw00f@latest

# Verify installations
subfinder -version
dnsx -version
nuclei -version
```

---

## Quick Start (One-Command Setup)

### Automated Installation Script

```bash
# Download and run the automated setup
curl -fsSL https://raw.githubusercontent.com/begineer-py/MTC-Master-tools-combination-/main/scripts/quick_install.sh | bash

# Or manually:
wget https://raw.githubusercontent.com/begineer-py/MTC-Master-tools-combination-/main/scripts/quick_install.sh
chmod +x quick_install.sh
./quick_install.sh
```

### What the Script Does

1. ✅ Checks system requirements
2. ✅ Installs Docker and Docker Compose
3. ✅ Installs Conda and sets up Python environment
4. ✅ Installs Go and security tools
5. ✅ Clones the repository
6. ✅ Starts infrastructure services
7. ✅ Installs Python dependencies
8. ✅ Initializes database
9. ✅ Creates admin user
10. ✅ Starts all services

### Post-Installation Verification

```bash
# Check all services are running
docker compose ps
conda activate mtc_env
python manage.py check
```

---

## Detailed Installation

### Step 1: Repository Setup

```bash
# Clone the repository
git clone https://github.com/begineer-py/MTC-Master-tools-combination-.git
cd MTC-Master-tools-combination-

# Create necessary directories
mkdir -p logs scans data/proxies
```

### Step 2: Infrastructure Services

#### 2.1 Create Environment Configuration

```bash
# Create .env file for Docker services
cat > .env << 'EOF'
# Database Configuration
POSTGRES_USER=myuser
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=mydb

# Hasura Configuration
HASURA_GRAPHQL_ADMIN_SECRET=CHANGE_THIS_SECRET
HASURA_GRAPHQL_DATABASE_URL=postgres://myuser:CHANGE_THIS_PASSWORD@postgres:5432/mydb

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Configuration
DJANGO_SECRET_KEY=CHANGE_THIS_SECRET_KEY
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# AI Services Configuration
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# Security Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
```

#### 2.2 Update Docker Compose Configuration

```bash
# Update docker-compose.yml with environment variables
sed -i 's/POSTGRES_PASSWORD: secret/POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}/' docker/docker-compose.yml
sed -i 's/HASURA_GRAPHQL_ADMIN_SECRET: "YourSuperStrongAdminSecretHere"/HASURA_GRAPHQL_ADMIN_SECRET: ${HASURA_GRAPHQL_ADMIN_SECRET}/' docker/docker-compose.yml
```

#### 2.3 Start Infrastructure Services

```bash
# Start all Docker services
cd docker
docker compose up -d

# Wait for services to be ready
sleep 30

# Check service health
docker compose ps
docker compose logs postgres | tail -10
docker compose logs redis | tail -10
```

### Step 3: Python Environment Setup

#### 3.1 Create Conda Environment

```bash
# Create Python 3.10 environment
conda create -n mtc_env python=3.10 -y

# Activate environment
conda activate mtc_env

# Upgrade pip
pip install --upgrade pip
```

#### 3.2 Install Python Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install additional dependencies for full functionality
pip install -r requirements/requirements.txt

# Verify installation
python -c "import django; print(f'Django {django.get_version()}')"
python -c "import celery; print(f'Celery {celery.__version__}')"
```

### Step 4: Database Initialization

#### 4.1 Run Database Migrations

```bash
# Apply all migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

#### 4.2 Create Superuser

```bash
# Create admin user interactively
python manage.py createsuperuser

# Or create non-interactively (for automation)
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
EOF
```

#### 4.3 Load Initial Data (Optional)

```bash
# Load sample data if available
python manage.py loaddata fixtures/initial_data.json
```

### Step 5: External Tools Configuration

#### 5.1 Configure AI Proxy Services

```bash
# Create proxy configuration
cat > docker/config.yaml << 'EOF'
proxies:
  - name: "gemini_json_ai"
    url: "http://localhost:8502/api/gemini_json_ai/"
    timeout: 30
    retries: 3
  - name: "mistral_ai"
    url: "http://localhost:8503/api/mistral_ai/"
    timeout: 30
    retries: 3
EOF
```

#### 5.2 Update Nuclei Templates

```bash
# Update Nuclei templates
nuclei -update-templates

# Verify templates
nuclei -stats
```

### Step 6: Service Startup

#### 6.1 Start Django API Server

```bash
# Terminal 1: Start Django with Uvicorn
conda activate mtc_env
uvicorn c2_core.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 9 \
    --loop uvloop \
    --http httptools \
    --backlog 2048 \
    --limit-concurrency 1000 \
    --reload
```

#### 6.2 Start Celery Worker

```bash
# Terminal 2: Start Celery Worker
conda activate mtc_env
python scripts/celery_worker_eventlet.py \
    -A c2_core.celery:app \
    worker \
    -P eventlet \
    -c 100 \
    -l info
```

#### 6.3 Start Celery Beat Scheduler

```bash
# Terminal 3: Start Celery Beat
conda activate mtc_env
celery -A c2_core beat -l info
```

#### 6.4 Start Frontend (Optional)

```bash
# Terminal 4: Start React Frontend
cd frontend
npm install
npm run dev
```

---

## Configuration & Security

### Environment Variables

Create a comprehensive `.env` file:

```bash
cat > .env << 'EOF'
# === Database Configuration ===
POSTGRES_USER=myuser
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=mydb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# === Django Configuration ===
DJANGO_SECRET_KEY=CHANGE_THIS_SECRET_KEY
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DJANGO_SETTINGS_MODULE=c2_core.settings

# === Redis Configuration ===
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# === Hasura Configuration ===
HASURA_GRAPHQL_ADMIN_SECRET=CHANGE_THIS_SECRET
HASURA_GRAPHQL_DATABASE_URL=postgres://myuser:CHANGE_THIS_PASSWORD@localhost:5432/mydb

# === AI Services Configuration ===
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# === Security Configuration ===
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://your-domain.com
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

# === Logging Configuration ===
LOG_LEVEL=INFO
LOG_FILE=logs/c2_django.log

# === Scanning Configuration ===
MAX_CONCURRENT_SCANS=10
SCAN_TIMEOUT=300
NMAP_OPTIONS=-sS -sV -O --max-retries 3
EOF
```

### Security Hardening

#### 1. Database Security

```bash
# Create database user with limited privileges
docker exec postgres psql -U myuser -d mydb -c "
CREATE USER scanner_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO scanner_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO scanner_user;
"
```

#### 2. Firewall Configuration

```bash
# Configure UFW (Ubuntu)
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django API (internal only)
sudo ufw deny 5432/tcp   # PostgreSQL (external access blocked)
sudo ufw deny 6379/tcp   # Redis (external access blocked)
```

#### 3. SSL/TLS Configuration

```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt for production
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 4. Django Security Settings

Update `settings.py`:

```python
# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

---

## Verification & Testing

### Health Checks

#### 1. Infrastructure Health

```bash
# Check Docker services
docker compose ps

# Check service logs
docker compose logs postgres
docker compose logs redis
docker compose logs hasura

# Test database connectivity
docker exec postgres pg_isready -U myuser
```

#### 2. Application Health

```bash
# Django system check
python manage.py check

# Test database connection
python manage.py dbshell -c "\l"

# Check Celery workers
celery -A c2_core inspect active
celery -A c2_core inspect stats
```

#### 3. API Endpoints Testing

```bash
# Test Django API
curl -I http://127.0.0.1:8000/api/

# Test Hasura GraphQL
curl -X POST http://127.0.0.1:8085/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name } } }"}'

# Test NocoDB
curl -I http://127.0.0.1:8081
```

### Functional Testing

#### 1. Create Test Target

```bash
# Create test target via Django admin
python manage.py shell << 'EOF'
from apps.core.models import Target, Seed
target = Target.objects.create(name="example.com", description="Test target")
seed = Seed.objects.create(target=target, value="example.com", type="domain")
print(f"Created target: {target.name}")
print(f"Created seed: {seed.value}")
EOF
```

#### 2. Run Test Scans

```bash
# Test subdomain discovery
python manage.py shell << 'EOF'
from apps.subfinder.tasks import run_subfinder_scan
from apps.core.models import Seed
seed = Seed.objects.first()
result = run_subfinder_scan.delay(seed.id)
print(f"Subfinder scan task ID: {result.id}")
EOF

# Test port scanning
python manage.py shell << 'EOF'
from apps.nmap_scanner.tasks import run_nmap_scan
from apps.core.models import Seed
seed = Seed.objects.first()
result = run_nmap_scan.delay(seed.id)
print(f"Nmap scan task ID: {result.id}")
EOF
```

#### 3. Verify Results

```bash
# Check scan results
python manage.py shell << 'EOF'
from apps.core.models import Subdomain, Port, SubfinderScan, NmapScan
print(f"Subdomains found: {Subdomain.objects.count()}")
print(f"Ports found: {Port.objects.count()}")
print(f"Subfinder scans: {SubfinderScan.objects.count()}")
print(f"Nmap scans: {NmapScan.objects.count()}")
EOF
```

### Performance Testing

#### 1. Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API performance
ab -n 1000 -c 10 http://127.0.0.1:8000/api/

# Test GraphQL performance
ab -n 1000 -c 10 -p test_graphql.json -T application/json http://127.0.0.1:8085/v1/graphql
```

#### 2. Database Performance

```bash
# Check database performance
docker exec postgres psql -U myuser -d mydb -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables;
"
```

---

## Operations & Maintenance

### Monitoring

#### 1. Application Monitoring

```bash
# Monitor Django logs
tail -f logs/c2_django.log

# Monitor Celery tasks
celery -A c2_core events

# Monitor system resources
htop
iostat -x 1
```

#### 2. Database Monitoring

```bash
# Monitor PostgreSQL
docker exec postgres psql -U myuser -d mydb -c "
SELECT
    state,
    count(*)
FROM pg_stat_activity
GROUP BY state;
"

# Monitor Redis
docker exec redis redis-cli info stats
```

#### 3. Docker Monitoring

```bash
# Monitor container resources
docker stats

# Monitor container logs
docker compose logs -f
```

### Backup & Recovery

#### 1. Database Backup

```bash
# Create backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# Create database backup
docker exec postgres pg_dump -U myuser mydb > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "Backup created: ${BACKUP_FILE}.gz"

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x scripts/backup_database.sh
```

#### 2. Data Recovery

```bash
# Create restore script
cat > scripts/restore_database.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE=$1

# Stop application services
docker compose stop hasura nocodb

# Restore database
gunzip -c $BACKUP_FILE | docker exec -i postgres psql -U myuser mydb

# Restart services
docker compose start hasura nocodb

echo "Database restored from $BACKUP_FILE"
EOF

chmod +x scripts/restore_database.sh
```

#### 3. Configuration Backup

```bash
# Backup configuration files
tar -czf backups/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    docker/ \
    .env \
    requirements.txt \
    environment.yml
```

### Regular Maintenance

#### 1. Database Maintenance

```bash
# Create maintenance script
cat > scripts/database_maintenance.sh << 'EOF'
#!/bin/bash

# Update statistics
docker exec postgres psql -U myuser -d mydb -c "ANALYZE;"

# Reindex database
docker exec postgres psql -U myuser -d mydb -c "REINDEX DATABASE mydb;"

# Clean up old sessions
docker exec postgres psql -U myuser -d mydb -c "
DELETE FROM django_session
WHERE expire_date < NOW() - INTERVAL '7 days';
"

echo "Database maintenance completed"
EOF

chmod +x scripts/database_maintenance.sh
```

#### 2. Log Rotation

```bash
# Create logrotate configuration
sudo cat > /etc/logrotate.d/c2-django << 'EOF'
/path/to/c2-django/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        docker compose restart
    endscript
}
EOF
```

#### 3. System Updates

```bash
# Create update script
cat > scripts/system_update.sh << 'EOF'
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull

# Restart services with new images
docker compose up -d

# Update Python packages
conda activate mtc_env
pip install --upgrade -r requirements.txt

# Update Go tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

echo "System update completed"
EOF

chmod +x scripts/system_update.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Docker Services Won't Start

**Problem**: Docker containers fail to start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker compose logs postgres
docker compose logs redis

# Check port conflicts
sudo netstat -tulpn | grep :5432
sudo netstat -tulpn | grep :6379
```

**Solution**:

```bash
# Reset Docker environment
docker compose down -v
docker system prune -f
docker compose up -d
```

#### 2. Django Migration Errors

**Problem**: Database migrations fail

```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (last resort)
python manage.py migrate core zero
python manage.py migrate
```

**Solution**:

```bash
# Fix migration conflicts
python manage.py migrate --fake
python manage.py migrate
```

#### 3. Celery Workers Not Responding

**Problem**: Celery tasks not processing

```bash
# Check Celery status
celery -A c2_core inspect active
celery -A c2_core inspect stats

# Check Redis connection
redis-cli ping
```

**Solution**:

```bash
# Restart Celery services
pkill -f celery
celery -A c2_core purge
# Restart workers
```

#### 4. External Tools Not Found

**Problem**: Security tools not in PATH

```bash
# Check tool availability
which nmap
which subfinder
which nuclei

# Check Go environment
echo $PATH
go env GOPATH
```

**Solution**:

```bash
# Fix PATH
export PATH=$PATH:~/go/bin
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
source ~/.bashrc
```

#### 5. AI Service Connection Errors

**Problem**: Cannot connect to AI services

```bash
# Test API connectivity
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Check proxy configuration
curl http://localhost:8502/api/gemini_json_ai/
```

**Solution**:

```bash
# Update API keys and proxy configuration
# Check network connectivity
# Verify proxy service is running
```

### Debug Mode

#### Enable Debug Logging

```bash
# Update Django settings
export DJANGO_DEBUG=true
export LOG_LEVEL=DEBUG

# Enable verbose logging
python manage.py runserver --verbosity=2
```

#### Database Debugging

```bash
# Enable query logging
docker exec postgres psql -U myuser -d mydb -c "
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();
"
```

#### Network Debugging

```bash
# Check service connectivity
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# Test API endpoints
curl -v http://127.0.0.1:8000/api/
curl -v http://127.0.0.1:8085/health
```

### Performance Issues

#### High Memory Usage

```bash
# Monitor memory usage
free -h
docker stats

# Check for memory leaks
valgrind --tool=memcheck python manage.py runserver
```

#### Slow Database Queries

```bash
# Identify slow queries
docker exec postgres psql -U myuser -d mydb -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

#### High CPU Usage

```bash
# Monitor CPU usage
top
htop

# Profile Django application
python -m cProfile -o profile.stats manage.py runserver
```

---

## Advanced Configuration

### Custom Scanning Profiles

#### 1. Nmap Profiles

Create custom Nmap profiles in `settings.py`:

```python
NMAP_PROFILES = {
    'quick': {
        'options': '-sS --top-ports 1000',
        'timeout': 300,
        'max_retries': 2
    },
    'comprehensive': {
        'options': '-sS -sV -O --script=default,safe',
        'timeout': 1800,
        'max_retries': 3
    },
    'stealth': {
        'options': '-sS -f -mtu 24 -T2',
        'timeout': 600,
        'max_retries': 1
    }
}
```

#### 2. Nuclei Templates

Configure Nuclei template usage:

```python
NUCLEI_CONFIG = {
    'templates': [
        'cves/',
        'vulnerabilities/',
        'misconfiguration/',
        'technologies/'
    ],
    'exclude': [
        'dos/',
        'intrusive/'
    ],
    'rate_limit': 10,
    'timeout': 300
}
```

### Multi-Environment Deployment

#### 1. Development Environment

```bash
# docker-compose.dev.yml
version: "3.8"
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: dev_db

  redis:
    ports:
      - "127.0.0.1:6379:6379"
```

#### 2. Production Environment

```bash
# docker-compose.prod.yml
version: "3.8"
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - django
```

### Custom AI Integration

#### 1. Add New AI Provider

```python
# analyze_ai/providers/custom_ai.py
import requests
from typing import Dict, Any

class CustomAIProvider:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{self.base_url}/analyze',
            json=data,
            headers=headers
        )

        return response.json()
```

#### 2. Register Provider

```python
# analyze_ai/settings.py
AI_PROVIDERS = {
    'custom_ai': {
        'class': 'analyze_ai.providers.custom_ai.CustomAIProvider',
        'config': {
            'api_key': os.getenv('CUSTOM_AI_API_KEY'),
            'base_url': os.getenv('CUSTOM_AI_BASE_URL')
        }
    }
}
```

### Custom Dashboard Integration

#### 1. Grafana Dashboard

```bash
# Add Grafana to docker-compose.yml
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  ports:
    - "127.0.0.1:3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    - ./grafana/datasources:/etc/grafana/provisioning/datasources
```

#### 2. Prometheus Metrics

Add Prometheus metrics to Django:

```python
# c2_core/middleware.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('django_requests_total', 'Total Django requests', ['method', 'path'])
REQUEST_DURATION = Histogram('django_request_duration_seconds', 'Django request duration')

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        REQUEST_COUNT.labels(method=request.method, path=request.path).inc()

        with REQUEST_DURATION.time():
            response = self.get_response(request)

        return response
```

---

## Security Hardening

### Network Security

#### 1. Firewall Rules

```bash
# Advanced UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH (rate limited)
sudo ufw limit 22/tcp

# Web services
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Internal services (restricted)
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 172.16.0.0/12 to any port 8000
sudo ufw allow from 192.168.0.0/16 to any port 8000
```

#### 2. Intrusion Detection

```bash
# Install and configure fail2ban
sudo apt install fail2ban

# Create jail configuration
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security

#### 1. Input Validation

```python
# core/validators.py
import re
from django.core.exceptions import ValidationError

def validate_domain(value):
    """Validate domain name format"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid domain name format')

def validate_ip_address(value):
    """Validate IP address format"""
    import ipaddress
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError('Invalid IP address format')
```

#### 2. Rate Limiting

```python
# core/middleware.py
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)

        # Check rate limit
        cache_key = f'rate_limit:{client_ip}'
        requests = cache.get(cache_key, 0)

        if requests >= 100:  # 100 requests per minute
            return HttpResponseTooManyRequests("Rate limit exceeded")

        # Increment counter
        cache.set(cache_key, requests + 1, 60)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

#### 3. Security Headers

```python
# c2_core/settings.py
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

# Add to middleware response
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        for header, value in SECURITY_HEADERS.items():
            response[header] = value

        return response
```

### Data Protection

#### 1. Encryption at Rest

```bash
# Enable disk encryption (LUKS)
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup luksOpen /dev/sdX encrypted_data
sudo mkfs.ext4 /dev/mapper/encrypted_data
sudo mount /dev/mapper/encrypted_data /mnt/encrypted
```

#### 2. Database Encryption

```python
# Encrypt sensitive data in database
from cryptography.fernet import Fernet
import base64

class EncryptedField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.cipher.decrypt(value.encode()).decode()

    def to_python(self, value):
        if isinstance(value, str):
            return value
        return self.cipher.decrypt(value).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        return self.cipher.encrypt(value.encode()).decode()
```

### Audit Logging

#### 1. Comprehensive Logging

```python
# core/audit.py
import logging
import json
from django.contrib.admin.models import LogEntry

audit_logger = logging.getLogger('audit')

class AuditLogger:
    @staticmethod
    def log_action(user, action, obj, details=None):
        """Log user actions for audit trail"""
        audit_data = {
            'user': user.username,
            'action': action,
            'object_type': obj.__class__.__name__,
            'object_id': obj.pk,
            'timestamp': timezone.now().isoformat(),
            'ip_address': get_client_ip(),
            'details': details or {}
        }

        # Log to file
        audit_logger.info(json.dumps(audit_data))

        # Log to Django admin
        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            action_flag=action,
            change_message=json.dumps(details)
        )
```

#### 2. Security Monitoring

```bash
# Create security monitoring script
cat > scripts/security_monitor.sh << 'EOF'
#!/bin/bash

# Monitor failed login attempts
tail -f /var/log/auth.log | grep "Failed password" | while read line; do
    echo "$(date): $line" >> /var/log/security_monitor.log
done

# Monitor suspicious Django activity
tail -f logs/c2_django.log | grep -i "error\|exception\|forbidden" | while read line; do
    echo "$(date): $line" >> /var/log/security_monitor.log
done
EOF

chmod +x scripts/security_monitor.sh
```

---

## 🎯 Conclusion

This comprehensive build guide provides everything needed to successfully deploy, configure, and maintain the C2 Django AI platform. Key takeaways:

### ✅ **Successful Deployment Checklist**

- [ ] All prerequisites installed (Docker, Conda, Go tools)
- [ ] Infrastructure services running (PostgreSQL, Redis, Hasura)
- [ ] Django application configured and started
- [ ] Celery workers processing tasks
- [ ] External tools accessible (Nmap, Subfinder, Nuclei)
- [ ] Security configurations applied
- [ ] Monitoring and logging enabled
- [ ] Backup procedures established

### 🔧 **Ongoing Maintenance**

- Regular system updates
- Database maintenance and optimization
- Log rotation and cleanup
- Security monitoring and patching
- Performance tuning and optimization

### 🚀 **Next Steps**

- Explore the API documentation
- Configure custom scanning profiles
- Set up automated monitoring
- Implement additional security measures
- Scale for production workloads

For support and updates, refer to the project repository and community forums.

---

**⚠️ Remember**: This platform is designed for authorized security testing only. Always ensure proper authorization before scanning any targets.
