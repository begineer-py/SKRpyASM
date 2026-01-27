#!/bin/bash

# C2 Django AI - Database Backup Script

set -e

# Configuration
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"
RETENTION_DAYS=7

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

# Create backup directory
mkdir -p $BACKUP_DIR

print_status "Starting database backup..."

# Check if PostgreSQL container is running
if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    print_error "PostgreSQL container is not running"
    exit 1
fi

# Create database backup
print_status "Creating database backup..."
if docker compose -f docker/docker-compose.yml exec -T postgres pg_dump -U myuser mydb > $BACKUP_FILE; then
    print_success "Database backup created: $BACKUP_FILE"
else
    print_error "Failed to create database backup"
    exit 1
fi

# Compress backup
print_status "Compressing backup..."
if gzip $BACKUP_FILE; then
    print_success "Backup compressed: $COMPRESSED_FILE"
else
    print_error "Failed to compress backup"
    exit 1
fi

# Verify backup file
if [ -f "$COMPRESSED_FILE" ] && [ -s "$COMPRESSED_FILE" ]; then
    BACKUP_SIZE=$(du -h $COMPRESSED_FILE | cut -f1)
    print_success "Backup verified. Size: $BACKUP_SIZE"
else
    print_error "Backup file is empty or missing"
    exit 1
fi

# Clean old backups
print_status "Cleaning old backups (keeping last $RETENTION_DAYS days)..."
REMOVED_COUNT=$(find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ $REMOVED_COUNT -gt 0 ]; then
    print_success "Removed $REMOVED_COUNT old backup files"
else
    print_status "No old backups to remove"
fi

# List all backups
print_status "Current backups:"
ls -lh $BACKUP_DIR/postgres_backup_*.sql.gz 2>/dev/null || print_warning "No backups found"

print_success "Backup process completed successfully!"

# Optional: Upload to cloud storage (uncomment and configure)
# print_status "Uploading backup to cloud storage..."
# aws s3 cp $COMPRESSED_FILE s3://your-backup-bucket/database/
# print_success "Backup uploaded to cloud storage"