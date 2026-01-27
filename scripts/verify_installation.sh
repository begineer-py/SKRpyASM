#!/bin/bash

# C2 Django AI - Installation Verification Script

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test service connectivity
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    print_status "Testing $service_name at $url..."
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        print_success "$service_name is responding correctly"
        return 0
    else
        print_error "$service_name is not responding correctly"
        return 1
    fi
}

# Function to check Docker services
check_docker_services() {
    print_status "Checking Docker services..."
    
    cd "$PROJECT_DIR/docker"
    
    # Check if all services are running
    local services_running=$(docker compose ps --services --filter "status=running" | wc -l)
    local services_total=$(docker compose ps --services | wc -l)
    
    if [ "$services_running" -eq "$services_total" ]; then
        print_success "All $services_total Docker services are running"
    else
        print_warning "$services_running/$services_total Docker services are running"
        docker compose ps
    fi
    
    # Check individual service health
    local services=("postgres" "redis" "hasura" "nocodb" "flaresolverr")
    
    for service in "${services[@]}"; do
        if docker compose ps "$service" | grep -q "Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
        fi
    done
    
    cd ..
}

# Function to check Python environment
check_python_environment() {
    print_status "Checking Python environment..."
    
    # Check if conda environment exists
    if ! conda env list | grep -q "mtc_env"; then
        print_error "Conda environment 'mtc_env' not found"
        return 1
    fi
    
    print_success "Conda environment 'mtc_env' found"
    
    # Activate environment and check packages
    source ~/miniconda3/bin/activate mtc_env
    
    # Check Django
    if python -c "import django; print(f'Django {django.get_version()}')" 2>/dev/null; then
        print_success "Django is installed and working"
    else
        print_error "Django is not working properly"
    fi
    
    # Check Celery
    if python -c "import celery; print(f'Celery {celery.__version__}')" 2>/dev/null; then
        print_success "Celery is installed and working"
    else
        print_error "Celery is not working properly"
    fi
    
    # Check other key packages
    local packages=("psycopg2" "redis" "requests" "beautifulsoup4" "pydantic")
    
    for package in "${packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            print_success "$package is installed"
        else
            print_error "$package is not installed"
        fi
    done
}

# Function to check Go tools
check_go_tools() {
    print_status "Checking Go tools..."
    
    local tools=("subfinder" "dnsx" "nuclei" "httpx" "naabu" "cdncheck" "wafw00f")
    
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            local version=$($tool -version 2>/dev/null || echo "unknown version")
            print_success "$tool is installed ($version)"
        else
            print_error "$tool is not installed or not in PATH"
        fi
    done
}

# Function to check system tools
check_system_tools() {
    print_status "Checking system tools..."
    
    local tools=("docker" "docker-compose" "conda" "nmap" "git" "curl" "wget")
    
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            local version=$($tool --version 2>/dev/null | head -1 || echo "unknown version")
            print_success "$tool is installed ($version)"
        else
            print_error "$tool is not installed"
        fi
    done
}

# Function to test database connectivity
test_database() {
    print_status "Testing database connectivity..."
    
    cd "$PROJECT_DIR/docker"
    
    # Test PostgreSQL connection
    if docker compose exec postgres pg_isready -U myuser >/dev/null 2>&1; then
        print_success "PostgreSQL is ready and accepting connections"
        
        # Test database access
        if docker compose exec postgres psql -U myuser -d mydb -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database access is working"
        else
            print_error "Database access failed"
        fi
    else
        print_error "PostgreSQL is not ready"
    fi
    
    cd ..
}

# Function to test Django application
test_django_app() {
    print_status "Testing Django application..."
    
    cd "$PROJECT_DIR"
    
    # Activate conda environment
    source ~/miniconda3/bin/activate mtc_env
    
    # Run Django system check
    if python manage.py check >/dev/null 2>&1; then
        print_success "Django system check passed"
    else
        print_error "Django system check failed"
        python manage.py check
    fi
    
    # Test database migrations
    if python manage.py showmigrations --plan >/dev/null 2>&1; then
        print_success "Django migrations are accessible"
    else
        print_error "Django migrations are not accessible"
    fi
    
    cd ..
}

# Function to test API endpoints
test_api_endpoints() {
    print_status "Testing API endpoints..."
    
    # Test Django API (if running)
    if curl -s http://127.0.0.1:8000/ >/dev/null 2>&1; then
        test_service "Django API" "http://127.0.0.1:8000/"
    else
        print_warning "Django API is not running (expected if not started)"
    fi
    
    # Test Hasura Console
    test_service "Hasura Console" "http://127.0.0.1:8085/console"
    
    # Test NocoDB
    test_service "NocoDB" "http://127.0.0.1:8081/"
    
    # Test FlareSolverr
    test_service "FlareSolverr" "http://127.0.0.1:8191/v1"
}

# Function to check configuration files
check_configuration() {
    print_status "Checking configuration files..."
    
    cd "$PROJECT_DIR"
    
    # Check .env file
    if [ -f ".env" ]; then
        print_success ".env file exists"
        
        # Check for required variables
        local required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "DJANGO_SECRET_KEY")
        
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" .env; then
                local value=$(grep "^$var=" .env | cut -d'=' -f2)
                if [ "$value" = "CHANGE_THIS_PASSWORD" ] || [ "$value" = "CHANGE_THIS_SECRET" ] || [ -z "$value" ]; then
                    print_warning "$var needs to be updated"
                else
                    print_success "$var is configured"
                fi
            else
                print_error "$var is missing from .env file"
            fi
        done
    else
        print_warning ".env file not found (copy from .env.example)"
    fi
    
    # Check docker-compose.yml
    if [ -f "docker/docker-compose.yml" ]; then
        print_success "docker-compose.yml exists"
    else
        print_error "docker-compose.yml not found"
    fi
    
    # Check requirements.txt
    if [ -f "requirements.txt" ]; then
        print_success "requirements.txt exists"
    else
        print_error "requirements.txt not found"
    fi
    
    cd ..
}

# Function to generate verification report
generate_report() {
    print_status "Generating verification report..."
    
    local report_file="verification_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "C2 Django AI Installation Verification Report"
        echo "Generated: $(date)"
        echo "=============================================="
        echo ""
        echo "System Information:"
        echo "OS: $(uname -s) $(uname -r)"
        echo "Architecture: $(uname -m)"
        echo "User: $(whoami)"
        echo "Directory: $(pwd)"
        echo ""
        echo "Docker Services:"
        cd "$PROJECT_DIR/docker"
        docker compose ps
        cd ..
        echo ""
        echo "Python Environment:"
        source ~/miniconda3/bin/activate mtc_env
        python --version
        pip list | grep -E "(Django|Celery|psycopg2|redis)"
        echo ""
        echo "Go Tools:"
        subfinder -version 2>/dev/null || echo "subfinder not found"
        nuclei -version 2>/dev/null || echo "nuclei not found"
        echo ""
        echo "Service URLs:"
        echo "Django API: http://127.0.0.1:8000"
        echo "Hasura Console: http://127.0.0.1:8085"
        echo "NocoDB: http://127.0.0.1:8081"
        echo "FlareSolverr: http://127.0.0.1:8191"
    } > "$report_file"
    
    print_success "Verification report saved to: $report_file"
}

# Main verification function
main() {
    print_status "Starting C2 Django AI installation verification..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Run verification checks
    check_system_tools
    check_docker_services
    check_python_environment
    check_go_tools
    test_database
    test_django_app
    check_configuration
    test_api_endpoints
    
    # Generate report
    generate_report
    
    print_success "Installation verification completed!"
    
    echo ""
    echo -e "${GREEN}=== Verification Summary ===${NC}"
    echo "✅ System tools checked"
    echo "✅ Docker services verified"
    echo "✅ Python environment verified"
    echo "✅ Go tools verified"
    echo "✅ Database connectivity tested"
    echo "✅ Django application tested"
    echo "✅ Configuration files checked"
    echo "✅ API endpoints tested"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Start Django API: ./start_django.sh"
    echo "2. Start Celery Worker: ./start_celery_worker.sh"
    echo "3. Start Celery Beat: ./start_celery_beat.sh"
    echo "4. Access services:"
    echo "   - Django Admin: http://127.0.0.1:8000/admin"
    echo "   - Hasura Console: http://127.0.0.1:8085"
    echo "   - NocoDB: http://127.0.0.1:8081"
    echo ""
    echo -e "${YELLOW}Remember to:${NC}"
    echo "- Update .env file with your API keys"
    echo "- Change default passwords"
    echo "- Configure security settings for production"
}

# Run main function
main "$@"