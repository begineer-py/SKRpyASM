#!/bin/bash

# C2 Django AI - Database Restore Script

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

# Function to show usage
show_usage() {
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/postgres_backup_20231201_120000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -lh backups/postgres_backup_*.sql.gz 2>/dev/null || echo "No backups found"
}

# Check arguments
if [ -z "$1" ]; then
    print_error "No backup file specified"
    show_usage
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    show_usage
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

print_status "Starting database restore from: $BACKUP_FILE"

# Check if PostgreSQL container is running
if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    print_error "PostgreSQL container is not running"
    print_status "Starting PostgreSQL container..."
    docker compose -f docker/docker-compose.yml up -d postgres
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Confirm restore operation
echo ""
print_warning "This will replace the current database with the backup."
echo -e "${YELLOW}Current data will be PERMANENTLY LOST!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    print_status "Restore operation cancelled"
    exit 0
fi

# Stop application services to prevent conflicts
print_status "Stopping application services..."
docker compose -f docker/docker-compose.yml stop hasura nocodb

# Determine if backup is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    print_status "Decompressing backup..."
    RESTORE_CMD="gunzip -c $BACKUP_FILE"
else
    RESTORE_CMD="cat $BACKUP_FILE"
fi

# Restore database
print_status "Restoring database..."
if $RESTORE_CMD | docker compose -f docker/docker-compose.yml exec -T postgres psql -U myuser -d mydb; then
    print_success "Database restored successfully"
else
    print_error "Failed to restore database"
    exit 1
fi

# Restart services
print_status "Restarting services..."
docker compose -f docker/docker-compose.yml start hasura nocodb

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Verify restore
print_status "Verifying restore..."
if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "SELECT COUNT(*) FROM django_migrations;" > /dev/null 2>&1; then
    print_success "Database verification passed"
else
    print_error "Database verification failed"
    exit 1
fi

# Run Django migrations to ensure schema is up to date
print_status "Running Django migrations..."
if command -v python >/dev/null 2>&1; then
    source ~/miniconda3/bin/activate mtc_env 2>/dev/null || true
    python manage.py migrate
    print_success "Django migrations completed"
else
    print_warning "Django not found in PATH. Please run migrations manually:"
    print_warning "conda activate mtc_env && python manage.py migrate"
fi

print_success "Database restore completed successfully!"
echo ""
echo "Next steps:"
echo "1. Verify data integrity in Django Admin: http://127.0.0.1:8000/admin"
echo "2. Check Hasura Console: http://127.0.0.1:8085"
echo "3. Test application functionality"