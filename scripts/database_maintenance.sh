#!/bin/bash

# C2 Django AI - Database Maintenance Script

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

# Change to project directory
cd "$PROJECT_DIR"

print_status "Starting database maintenance..."

# Check if PostgreSQL container is running
if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    print_error "PostgreSQL container is not running"
    exit 1
fi

# Update statistics
print_status "Updating database statistics..."
if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "ANALYZE;"; then
    print_success "Database statistics updated"
else
    print_error "Failed to update statistics"
fi

# Reindex database
print_status "Reindexing database..."
if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "REINDEX DATABASE mydb;"; then
    print_success "Database reindexed"
else
    print_error "Failed to reindex database"
fi

# Clean up old sessions
print_status "Cleaning up old Django sessions..."
if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
DELETE FROM django_session 
WHERE expire_date < NOW() - INTERVAL '7 days';
"; then
    DELETED_SESSIONS=$(docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -t -c "
SELECT COUNT(*) FROM django_session 
WHERE expire_date < NOW() - INTERVAL '7 days';
" | tr -d ' ')
    print_success "Cleaned up old sessions"
else
    print_error "Failed to clean up sessions"
fi

# Clean up old Celery task results
print_status "Cleaning up old Celery task results..."
if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
DELETE FROM celery_taskmeta 
WHERE date_done < NOW() - INTERVAL '7 days';
"; then
    print_success "Cleaned up old Celery task results"
else
    print_warning "Failed to clean up Celery results (table might not exist)"
fi

# Update table statistics for large tables
print_status "Updating statistics for large tables..."
TABLES=("core_subdomain" "core_port" "core_urlresult" "core_ip")

for table in "${TABLES[@]}"; do
    if docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "\dt $table" > /dev/null 2>&1; then
        print_status "Updating statistics for table: $table"
        docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "ANALYZE $table;"
    fi
done

# Check database size
print_status "Database size information:"
docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
SELECT 
    pg_database.datname AS database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE pg_database.datname = 'mydb';
"

# Check table sizes
print_status "Table size information:"
docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
"

# Check for database bloat
print_status "Checking for table bloat:"
docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty((pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename))) AS bloat_size
FROM pg_tables 
WHERE schemaname = 'public'
    AND (pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) > 100 * 1024 * 1024  -- Bloat > 100MB
ORDER BY (pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) DESC;
" || print_warning "No significant bloat detected or bloat check failed"

# Optimize autovacuum settings for large tables
print_status "Checking autovacuum settings..."
docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
SELECT 
    schemaname,
    tablename,
    autovacuum_enabled,
    autovacuum_vacuum_scale_factor,
    autovacuum_analyze_scale_factor
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5;
"

# Vacuum analyze if needed
print_status "Checking if VACUUM ANALYZE is needed..."
UNDEAD_TUPLES=$(docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -t -c "
SELECT SUM(n_dead_tup) FROM pg_stat_user_tables;
" | tr -d ' ')

TOTAL_TUPLES=$(docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -t -c "
SELECT SUM(n_live_tup) FROM pg_stat_user_tables;
" | tr -d ' ')

if [ -n "$UNDEAD_TUPLES" ] && [ -n "$TOTAL_TUPLES" ] && [ "$TOTAL_TUPLES" -gt 0 ]; then
    RATIO=$(echo "scale=2; $UNDEAD_TUPLES * 100 / $TOTAL_TUPLES" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$RATIO > 10" | bc -l 2>/dev/null || echo "0") )); then
        print_status "Running VACUUM ANALYZE (dead tuple ratio: ${RATIO}%)..."
        docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "VACUUM ANALYZE;"
        print_success "VACUUM ANALYZE completed"
    else
        print_status "VACUUM ANALYZE not needed (dead tuple ratio: ${RATIO}%)"
    fi
fi

# Check index usage
print_status "Checking index usage statistics:"
docker compose -f docker/docker-compose.yml exec postgres psql -U myuser -d mydb -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT 10;
"

print_success "Database maintenance completed successfully!"

# Suggest next maintenance
echo ""
print_status "Recommendations:"
echo "1. Run this script weekly for optimal performance"
echo "2. Monitor database growth and consider partitioning large tables"
echo "3. Review query performance for slow queries"
echo "4. Consider setting up automated backups with the backup script"