#!/bin/bash

# C2 Django AI - System Update Script

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to detect package manager
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        PKG_MANAGER="apt"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
    else
        print_error "Unsupported package manager"
        exit 1
    fi
}

# Function to update system packages
update_system_packages() {
    print_status "Updating system packages using $PKG_MANAGER..."
    
    case $PKG_MANAGER in
        apt)
            sudo apt update
            sudo apt upgrade -y
            ;;
        yum)
            sudo yum update -y
            sudo yum upgrade -y
            ;;
        dnf)
            sudo dnf update -y
            sudo dnf upgrade -y
            ;;
    esac
    
    print_success "System packages updated"
}

# Function to update Docker images
update_docker_images() {
    print_status "Updating Docker images..."
    
    cd "$PROJECT_DIR/docker"
    
    # Pull updated images
    docker compose pull
    
    # Show what images were updated
    print_status "Checking for updated images..."
    docker images | grep -E "(postgres|redis|hasura|nocodb|flaresolverr)" | head -10
    
    print_success "Docker images updated"
}

# Function to restart Docker services with new images
restart_docker_services() {
    print_status "Restarting Docker services with updated images..."
    
    cd "$PROJECT_DIR/docker"
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        print_status "Stopping current services..."
        docker compose down
    fi
    
    # Start services with new images
    print_status "Starting services with updated images..."
    docker compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if docker compose ps | grep -q "Up"; then
        print_success "Docker services restarted successfully"
    else
        print_error "Some services failed to start"
        docker compose logs
        exit 1
    fi
}

# Function to update Python packages
update_python_packages() {
    print_status "Updating Python packages..."
    
    # Check if conda environment exists
    if ! conda env list | grep -q "mtc_env"; then
        print_warning "Conda environment 'mtc_env' not found. Skipping Python package updates."
        return
    fi
    
    # Activate conda environment
    source ~/miniconda3/bin/activate mtc_env
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Update requirements if available
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        pip install -r "$PROJECT_DIR/requirements.txt" --upgrade
    fi
    
    if [ -f "$PROJECT_DIR/requirements/requirements.txt" ]; then
        pip install -r "$PROJECT_DIR/requirements/requirements.txt" --upgrade
    fi
    
    print_success "Python packages updated"
}

# Function to update Go tools
update_go_tools() {
    print_status "Updating Go tools..."
    
    # Check if Go is installed
    if ! command -v go >/dev/null 2>&1; then
        print_warning "Go not found. Skipping Go tools update."
        return
    fi
    
    # Update Project Discovery tools
    print_status "Updating Project Discovery tools..."
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    go install -v github.com/projectdiscovery/dnsx/cmd/ddsx@latest
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
    go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest
    go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
    
    # Update other tools
    print_status "Updating other security tools..."
    go install -v github.com/Edu4rdSHL/wafw00f@latest
    
    # Update Nuclei templates
    if command -v nuclei >/dev/null 2>&1; then
        print_status "Updating Nuclei templates..."
        nuclei -update-templates
    fi
    
    print_success "Go tools updated"
}

# Function to run Django migrations
run_django_migrations() {
    print_status "Running Django migrations..."
    
    cd "$PROJECT_DIR"
    
    # Activate conda environment
    source ~/miniconda3/bin/activate mtc_env
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    until docker compose -f docker/docker-compose.yml exec postgres pg_isready -U myuser >/dev/null 2>&1; do
        sleep 2
    done
    
    # Run migrations
    python manage.py migrate
    
    print_success "Django migrations completed"
}

# Function to verify update
verify_update() {
    print_status "Verifying update..."
    
    # Check Docker services
    cd "$PROJECT_DIR/docker"
    print_status "Checking Docker services:"
    docker compose ps
    
    # Check Django health
    cd "$PROJECT_DIR"
    source ~/miniconda3/bin/activate mtc_env
    
    print_status "Running Django system check:"
    python manage.py check
    
    # Check Go tools
    print_status "Verifying Go tools:"
    echo "Subfinder: $(subfinder -version 2>/dev/null || echo 'Not found')"
    echo "Nuclei: $(nuclei -version 2>/dev/null || echo 'Not found')"
    echo "DNSx: $(dnsx -version 2>/dev/null || echo 'Not found')"
    
    print_success "System verification completed"
}

# Function to show update summary
show_summary() {
    print_success "System update completed successfully!"
    
    echo ""
    echo -e "${GREEN}=== Update Summary ===${NC}"
    echo -e "${BLUE}• System packages updated${NC}"
    echo -e "${BLUE}• Docker images updated${NC}"
    echo -e "${BLUE}• Docker services restarted${NC}"
    echo -e "${BLUE}• Python packages updated${NC}"
    echo -e "${BLUE}• Go tools updated${NC}"
    echo -e "${BLUE}• Django migrations applied${NC}"
    echo ""
    echo -e "${GREEN}=== Service Status ===${NC}"
    cd "$PROJECT_DIR/docker"
    docker compose ps
    echo ""
    echo -e "${YELLOW}Recommendations:${NC}"
    echo "1. Test application functionality"
    echo "2. Check logs for any errors: docker compose logs"
    echo "3. Run database maintenance: ./scripts/database_maintenance.sh"
    echo "4. Monitor system performance for next few hours"
}

# Main update function
main() {
    print_status "Starting system update..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Check for root privileges (needed for system updates)
    if [ "$EUID" -ne 0 ]; then
        print_warning "Some updates require sudo privileges. You may be prompted for password."
    fi
    
    # Run update steps
    detect_package_manager
    update_system_packages
    update_docker_images
    restart_docker_services
    update_python_packages
    update_go_tools
    run_django_migrations
    verify_update
    show_summary
    
    print_success "System update completed!"
}

# Run main function
main "$@"