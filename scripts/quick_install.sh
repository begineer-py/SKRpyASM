#!/bin/bash

# C2 Django AI - Quick Installation Script
# This script automates the entire installation process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    
    if command_exists docker; then
        print_warning "Docker is already installed. Skipping..."
        return
    fi
    
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Install docker-compose plugin
    if command_exists apt; then
        sudo apt update
        sudo apt install -y docker-compose-plugin
    elif command_exists yum; then
        sudo yum install -y docker-compose-plugin
    elif command_exists dnf; then
        sudo dnf install -y docker-compose-plugin
    fi
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    rm get-docker.sh
    print_success "Docker installed successfully"
}

# Function to install Conda
install_conda() {
    print_status "Installing Miniconda..."
    
    if command_exists conda; then
        print_warning "Conda is already installed. Skipping..."
        return
    fi
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    elif [ "$ARCH" = "aarch64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
    else
        print_error "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    wget $MINICONDA_URL -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda3
    
    # Initialize conda
    $HOME/miniconda3/bin/conda init bash
    source ~/.bashrc
    
    rm miniconda.sh
    print_success "Miniconda installed successfully"
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if command_exists apt; then
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
            golang-go \
            htop \
            netstat
    elif command_exists yum; then
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
            golang \
            htop \
            net-tools
    elif command_exists dnf; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y \
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
            golang \
            htop \
            net-tools
    else
        print_error "Unsupported package manager. Please install dependencies manually."
        exit 1
    fi
    
    print_success "System dependencies installed"
}

# Function to install Go tools
install_go_tools() {
    print_status "Installing Go tools..."
    
    # Set up Go environment
    export PATH=$PATH:~/go/bin
    echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
    
    # Create go bin directory
    mkdir -p ~/go/bin
    
    # Install Project Discovery tools
    print_status "Installing Project Discovery tools..."
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
    go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest
    go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
    
    # Install other security tools
    print_status "Installing other security tools..."
    go install -v github.com/Edu4rdSHL/wafw00f@latest
    
    # Update Nuclei templates
    if command_exists nuclei; then
        print_status "Updating Nuclei templates..."
        nuclei -update-templates
    fi
    
    print_success "Go tools installed"
}

# Function to clone repository
clone_repository() {
    print_status "Cloning C2 Django AI repository..."
    
    if [ -d "MTC-Master-tools-combination-" ]; then
        print_warning "Repository already exists. Updating..."
        cd MTC-Master-tools-combination-
        git pull origin main
        cd ..
    else
        git clone https://github.com/begineer-py/MTC-Master-tools-combination-.git
    fi
    
    cd MTC-Master-tools-combination-
    
    # Create necessary directories
    mkdir -p logs scans data/proxies
    
    cd ..
    print_success "Repository cloned/updated"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    cd MTC-Master-tools-combination-
    
    # Generate secure passwords and keys
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    HASURA_SECRET=$(openssl rand -base64 32)
    DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Create .env file
    cat > .env << EOF
# Database Configuration
POSTGRES_USER=myuser
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=mydb

# Hasura Configuration
HASURA_GRAPHQL_ADMIN_SECRET=$HASURA_SECRET
HASURA_GRAPHQL_DATABASE_URL=postgres://myuser:$POSTGRES_PASSWORD@postgres:5432/mydb

# Django Configuration
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# AI Services Configuration
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# Security Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
    
    # Create proxy configuration
    mkdir -p docker
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
    
    print_success "Environment configured"
}

# Function to start infrastructure
start_infrastructure() {
    print_status "Starting infrastructure services..."
    
    cd MTC-Master-tools-combination-
    cd docker
    
    # Start all services
    docker compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service health
    if docker compose ps | grep -q "Up"; then
        print_success "Infrastructure services started successfully"
    else
        print_error "Some services failed to start. Check logs with: docker compose logs"
        exit 1
    fi
    
    cd ..
    cd ..
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    cd MTC-Master-tools-combination-
    
    # Activate conda
    source ~/miniconda3/bin/activate
    
    # Create conda environment
    conda create -n mtc_env python=3.10 -y
    conda activate mtc_env
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    if [ -f "requirements/requirements.txt" ]; then
        pip install -r requirements/requirements.txt
    fi
    
    cd ..
    print_success "Python environment setup completed"
}

# Function to initialize database
init_database() {
    print_status "Initializing database..."
    
    cd MTC-Master-tools-combination-
    
    # Activate conda environment
    source ~/miniconda3/bin/activate mtc_env
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    until docker compose -f docker/docker-compose.yml exec postgres pg_isready -U myuser; do
        sleep 2
    done
    
    # Run migrations
    python manage.py migrate
    
    # Create superuser (non-interactive)
    python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser 'admin' created with password 'admin123'")
else:
    print("Superuser 'admin' already exists")
EOF
    
    # Run system check
    python manage.py check
    
    cd ..
    print_success "Database initialized"
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    cd MTC-Master-tools-combination-
    
    # Create Django startup script
    cat > start_django.sh << 'EOF'
#!/bin/bash
source ~/miniconda3/bin/activate mtc_env
uvicorn c2_core.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 9 \
    --loop uvloop \
    --http httptools \
    --backlog 2048 \
    --limit-concurrency 1000 \
    --reload
EOF
    
    # Create Celery worker script
    cat > start_celery_worker.sh << 'EOF'
#!/bin/bash
source ~/miniconda3/bin/activate mtc_env
python scripts/celery_worker_eventlet.py \
    -A c2_core.celery:app \
    worker \
    -P eventlet \
    -c 100 \
    -l info
EOF
    
    # Create Celery beat script
    cat > start_celery_beat.sh << 'EOF'
#!/bin/bash
source ~/miniconda3/bin/activate mtc_env
celery -A c2_core beat -l info
EOF
    
    # Make scripts executable
    chmod +x start_*.sh
    
    cd ..
    print_success "Startup scripts created"
}

# Function to create service scripts
create_service_scripts() {
    print_status "Creating systemd services..."
    
    cd MTC-Master-tools-combination-
    
    # Get current user and path
    USER=$(whoami)
    HOME_DIR=$(eval echo ~$USER)
    PROJECT_DIR=$(pwd)
    
    # Create Django service
    sudo tee /etc/systemd/system/c2-django.service > /dev/null << EOF
[Unit]
Description=C2 Django AI Application
After=docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$HOME_DIR/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PROJECT_DIR/start_django.sh
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create Celery worker service
    sudo tee /etc/systemd/system/c2-celery-worker.service > /dev/null << EOF
[Unit]
Description=C2 Django AI Celery Worker
After=docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$HOME_DIR/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PROJECT_DIR/start_celery_worker.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create Celery beat service
    sudo tee /etc/systemd/system/c2-celery-beat.service > /dev/null << EOF
[Unit]
Description=C2 Django AI Celery Beat
After=docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$HOME_DIR/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PROJECT_DIR/start_celery_beat.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    cd ..
    print_success "Systemd services created"
}

# Function to display final information
display_completion() {
    print_success "Installation completed successfully!"
    
    echo ""
    echo -e "${GREEN}=== Installation Summary ===${NC}"
    echo -e "${BLUE}Project Directory:${NC} $(pwd)/MTC-Master-tools-combination-"
    echo -e "${BLUE}Conda Environment:${NC} mtc_env"
    echo ""
    echo -e "${GREEN}=== Service Access Points ===${NC}"
    echo -e "${BLUE}Django API:${NC} http://127.0.0.1:8000"
    echo -e "${BLUE}Django Admin:${NC} http://127.0.0.1:8000/admin"
    echo -e "${BLUE}Hasura Console:${NC} http://127.0.0.1:8085"
    echo -e "${BLUE}NocoDB:${NC} http://127.0.0.1:8081"
    echo ""
    echo -e "${GREEN}=== Admin Credentials ===${NC}"
    echo -e "${BLUE}Username:${NC} admin"
    echo -e "${BLUE}Password:${NC} admin123"
    echo ""
    echo -e "${GREEN}=== Next Steps ===${NC}"
    echo "1. Update AI API keys in .env file"
    echo "2. Start services manually or use systemd:"
    echo "   sudo systemctl start c2-django"
    echo "   sudo systemctl start c2-celery-worker"
    echo "   sudo systemctl start c2-celery-beat"
    echo "3. Enable services to start on boot:"
    echo "   sudo systemctl enable c2-django"
    echo "   sudo systemctl enable c2-celery-worker"
    echo "   sudo systemctl enable c2-celery-beat"
    echo ""
    echo -e "${YELLOW}Important:${NC} Please change the default admin password and update .env file with your API keys!"
    echo ""
    echo -e "${BLUE}For detailed documentation, see:${NC} BUILD_GUIDE.md"
}

# Main installation function
main() {
    print_status "Starting C2 Django AI installation..."
    
    # Detect operating system
    detect_os
    print_status "Detected OS: $OS $VER"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root. Run as regular user."
        exit 1
    fi
    
    # Installation steps
    install_system_deps
    install_docker
    install_conda
    install_go_tools
    clone_repository
    setup_environment
    start_infrastructure
    setup_python_env
    init_database
    create_startup_scripts
    create_service_scripts
    
    display_completion
    
    print_success "Installation completed! Please log out and log back in to apply group changes."
}

# Run main function
main "$@"