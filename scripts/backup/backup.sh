#!/bin/bash
# Unified Backup Script for Threads Automation Tool
# Combines all backup scripts into one with menu

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# COMMON UTILITIES
# ============================================================================

# Load environment variables from .env file
load_env() {
    local env_file="${1:-.env}"
    if [ -f "${env_file}" ]; then
        export $(grep -v '^#' "${env_file}" | grep -v '^$' | xargs)
        return 0
    else
        echo -e "${YELLOW}Warning: .env file not found at ${env_file}${NC}" >&2
        return 1
    fi
}

# Get MySQL configuration with defaults
get_mysql_config() {
    MYSQL_HOST="${MYSQL_HOST:-localhost}"
    MYSQL_PORT="${MYSQL_PORT:-3306}"
    MYSQL_USER="${MYSQL_USER:-threads_user}"
    MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
    MYSQL_DATABASE="${MYSQL_DATABASE:-threads_analytics}"
    DOCKER_CONTAINER="${DOCKER_CONTAINER:-threads_mysql}"
}

# Validate MySQL configuration
validate_mysql_config() {
    if [ -z "${MYSQL_PASSWORD}" ]; then
        echo -e "${RED}ERROR: MYSQL_PASSWORD not set${NC}" >&2
        echo "Please set MYSQL_PASSWORD in .env file or environment variable." >&2
        exit 1
    fi
    
    if [ -z "${MYSQL_DATABASE}" ]; then
        echo -e "${RED}ERROR: MYSQL_DATABASE not set${NC}" >&2
        exit 1
    fi
}

# Check if Docker container exists
check_docker_container() {
    local container="${1:-${DOCKER_CONTAINER}}"
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container}$"; then
        return 0
    else
        return 1
    fi
}

# Logging function with timestamp
log() {
    local message="$1"
    local log_file="${2:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_message="[${timestamp}] ${message}"
    
    echo "${log_message}"
    
    if [ -n "${log_file}" ]; then
        echo "${log_message}" >> "${log_file}"
    fi
}

# Log error with red color
log_error() {
    local message="$1"
    local log_file="${2:-}"
    echo -e "${RED}${message}${NC}" >&2
    log "ERROR: ${message}" "${log_file}"
}

# Log success with green color
log_success() {
    local message="$1"
    local log_file="${2:-}"
    echo -e "${GREEN}${message}${NC}"
    log "SUCCESS: ${message}" "${log_file}"
}

# Log warning with yellow color
log_warning() {
    local message="$1"
    local log_file="${2:-}"
    echo -e "${YELLOW}${message}${NC}" >&2
    log "WARNING: ${message}" "${log_file}"
}

# Log info with blue color
log_info() {
    local message="$1"
    local log_file="${2:-}"
    echo -e "${BLUE}${message}${NC}"
    log "INFO: ${message}" "${log_file}"
}

# Print header
print_header() {
    local title="$1"
    local log_file="${2:-}"
    local width="${3:-60}"
    local line=$(printf '%*s' "${width}" | tr ' ' '=')
    
    log "${line}" "${log_file}"
    log "${title}" "${log_file}"
    log "${line}" "${log_file}"
}

# Get backup directory
get_backup_dir() {
    echo "${BACKUP_DIR:-./backups}"
}

# Ensure backup directory exists
ensure_backup_dir() {
    local backup_dir=$(get_backup_dir)
    mkdir -p "${backup_dir}"
    echo "${backup_dir}"
}

# Validate backup file exists and is readable
validate_backup_file() {
    local backup_file="$1"
    
    if [ -z "${backup_file}" ]; then
        log_error "Backup file path is empty"
        exit 1
    fi
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        exit 1
    fi
    
    if [ ! -r "${backup_file}" ]; then
        log_error "Backup file is not readable: ${backup_file}"
        exit 1
    fi
    
    # Check if file is compressed
    if [[ "${backup_file}" == *.gz ]]; then
        if ! gunzip -t "${backup_file}" 2>/dev/null; then
            log_error "Backup file is corrupted (gzip test failed): ${backup_file}"
            exit 1
        fi
    fi
}

# Get formatted date for backup filename
get_backup_date() {
    date +%Y%m%d_%H%M%S
}

# Cleanup old backups
cleanup_old_backups() {
    local backup_dir=$(get_backup_dir)
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    local log_file="${1:-}"
    
    log_info "Cleaning up old backups (older than ${retention_days} days)..." "${log_file}"
    
    local cleaned_count=0
    while IFS= read -r file; do
        if [ -f "${file}" ]; then
            rm -f "${file}"
            cleaned_count=$((cleaned_count + 1))
        fi
    done < <(find "${backup_dir}" -name "threads_backup_*.sql.gz" -type f -mtime +${retention_days} 2>/dev/null)
    
    if [ ${cleaned_count} -gt 0 ]; then
        log_success "Cleaned up ${cleaned_count} old backup(s)" "${log_file}"
    else
        log_info "No old backups to clean up" "${log_file}"
    fi
    
    return ${cleaned_count}
}

# ============================================================================
# MENU FUNCTIONS
# ============================================================================

show_menu() {
    echo ""
    echo "=========================================="
    echo "BACKUP & RESTORE MENU"
    echo "=========================================="
    echo ""
    echo "1. MySQL Backup"
    echo "2. Restore Backup"
    echo "3. Setup Cron Job"
    echo "4. List Backups"
    echo ""
    echo "0. Exit"
    echo ""
    read -p "Chọn option (0-4): " choice
    echo ""
    echo "$choice"
}

# ============================================================================
# BACKUP FUNCTION
# ============================================================================

mysql_backup() {
    # Load environment variables
    load_env
    
    # Get MySQL configuration
    get_mysql_config
    
    # Validate MySQL configuration
    validate_mysql_config
    
    # Configuration
    RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
    DATE=$(get_backup_date)
    BACKUP_DIR=$(ensure_backup_dir)
    BACKUP_FILE="${BACKUP_DIR}/threads_backup_${DATE}.sql.gz"
    LOG_FILE="${BACKUP_DIR}/backup_${DATE}.log"
    
    print_header "MySQL Backup Started" "${LOG_FILE}"
    log "Database: ${MYSQL_DATABASE}" "${LOG_FILE}"
    log "Backup file: ${BACKUP_FILE}" "${LOG_FILE}"
    log "Retention: ${RETENTION_DAYS} days" "${LOG_FILE}"
    
    # Check if Docker container exists
    if check_docker_container "${DOCKER_CONTAINER}"; then
        log_info "Using Docker container: ${DOCKER_CONTAINER}" "${LOG_FILE}"
        
        log_info "Starting backup..." "${LOG_FILE}"
        docker exec "${DOCKER_CONTAINER}" mysqldump \
            -u "${MYSQL_USER}" \
            -p"${MYSQL_PASSWORD}" \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            "${MYSQL_DATABASE}" | gzip > "${BACKUP_FILE}"
        
        BACKUP_EXIT_CODE=${PIPESTATUS[0]}
        
        if [ ${BACKUP_EXIT_CODE} -eq 0 ]; then
            BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
            log_success "Backup completed successfully" "${LOG_FILE}"
            log "Backup size: ${BACKUP_SIZE}" "${LOG_FILE}"
        else
            log_error "Backup failed with exit code ${BACKUP_EXIT_CODE}" "${LOG_FILE}"
            rm -f "${BACKUP_FILE}"
            exit 1
        fi
    else
        log_warning "Docker container not found, trying direct MySQL connection..." "${LOG_FILE}"
        
        log_info "Starting backup..." "${LOG_FILE}"
        mysqldump \
            -h "${MYSQL_HOST}" \
            -P "${MYSQL_PORT}" \
            -u "${MYSQL_USER}" \
            -p"${MYSQL_PASSWORD}" \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            "${MYSQL_DATABASE}" | gzip > "${BACKUP_FILE}"
        
        if [ $? -eq 0 ]; then
            BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
            log_success "Backup completed successfully" "${LOG_FILE}"
            log "Backup size: ${BACKUP_SIZE}" "${LOG_FILE}"
        else
            log_error "Backup failed" "${LOG_FILE}"
            rm -f "${BACKUP_FILE}"
            exit 1
        fi
    fi
    
    # Cleanup old backups
    cleanup_old_backups "${LOG_FILE}"
    
    # Verify backup file exists and has content
    if [ ! -f "${BACKUP_FILE}" ] || [ ! -s "${BACKUP_FILE}" ]; then
        log_error "Backup file is missing or empty" "${LOG_FILE}"
        exit 1
    fi
    
    # Summary
    REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "threads_backup_*.sql.gz" -type f 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
    
    print_header "Backup Summary" "${LOG_FILE}"
    log "Backup file: ${BACKUP_FILE}" "${LOG_FILE}"
    log "Total backups: ${REMAINING_BACKUPS}" "${LOG_FILE}"
    log "Total size: ${TOTAL_SIZE}" "${LOG_FILE}"
    print_header "MySQL Backup Completed Successfully" "${LOG_FILE}"
}

# ============================================================================
# RESTORE FUNCTION
# ============================================================================

restore_backup() {
    # Load environment variables
    load_env
    
    # Get MySQL configuration
    get_mysql_config
    
    # Validate MySQL configuration
    validate_mysql_config
    
    # Configuration
    BACKUP_DIR=$(get_backup_dir)
    
    # Check if backup file is provided
    if [ -z "$1" ]; then
        echo -e "${RED}Usage: restore_backup <backup_file.sql.gz>${NC}"
        echo ""
        echo "Available backups:"
        ls -lh "${BACKUP_DIR}"/threads_backup_*.sql.gz 2>/dev/null | awk '{print $9, "("$5")"}' || echo "No backups found"
        return 1
    fi
    
    BACKUP_FILE="$1"
    
    # Validate backup file
    validate_backup_file "${BACKUP_FILE}"
    
    # Confirm restore
    log_warning "WARNING: This will REPLACE the current database!"
    echo "Database: ${MYSQL_DATABASE}"
    echo "Backup file: ${BACKUP_FILE}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    
    if [ "${CONFIRM}" != "yes" ]; then
        log_info "Restore cancelled."
        return 0
    fi
    
    echo ""
    log_info "Starting restore..."
    
    # Check if Docker container exists
    if check_docker_container "${DOCKER_CONTAINER}"; then
        log_info "Using Docker container: ${DOCKER_CONTAINER}"
        
        # Restore from compressed backup
        gunzip < "${BACKUP_FILE}" | docker exec -i "${DOCKER_CONTAINER}" mysql \
            -u "${MYSQL_USER}" \
            -p"${MYSQL_PASSWORD}" \
            "${MYSQL_DATABASE}"
        
        if [ ${PIPESTATUS[0]} -eq 0 ] && [ ${PIPESTATUS[1]} -eq 0 ]; then
            log_success "Restore completed successfully!"
        else
            log_error "Restore failed"
            return 1
        fi
    else
        log_warning "Docker container not found, trying direct MySQL connection..."
        
        # Restore from compressed backup
        gunzip < "${BACKUP_FILE}" | mysql \
            -h "${MYSQL_HOST}" \
            -P "${MYSQL_PORT}" \
            -u "${MYSQL_USER}" \
            -p"${MYSQL_PASSWORD}" \
            "${MYSQL_DATABASE}"
        
        if [ ${PIPESTATUS[0]} -eq 0 ] && [ ${PIPESTATUS[1]} -eq 0 ]; then
            log_success "Restore completed successfully!"
        else
            log_error "Restore failed"
            return 1
        fi
    fi
    
    echo ""
    log_success "Restore completed successfully!"
}

# ============================================================================
# SETUP CRON FUNCTION
# ============================================================================

setup_cron() {
    BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
    CRON_TIME="0 2"  # 2:00 AM daily
    
    # Make backup script executable
    chmod +x "${BACKUP_SCRIPT}"
    
    # Create crontab entry
    CRON_ENTRY="${CRON_TIME} * * * ${BACKUP_SCRIPT} backup"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "${BACKUP_SCRIPT}"; then
        echo "Cron job already exists:"
        crontab -l | grep "${BACKUP_SCRIPT}"
        echo ""
        read -p "Do you want to update it? (yes/no): " UPDATE
        if [ "${UPDATE}" != "yes" ]; then
            echo "Cancelled."
            return 0
        fi
        # Remove existing entry
        crontab -l | grep -v "${BACKUP_SCRIPT}" | crontab -
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "${CRON_ENTRY}") | crontab -
    
    echo "Cron job added successfully!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "${BACKUP_SCRIPT}"
    echo ""
    echo "Backups will run daily at 2:00 AM"
    echo "Backup location: ./backups/"
    echo ""
    echo "To view cron logs: tail -f ./backups/backup_*.log"
}

# ============================================================================
# LIST BACKUPS FUNCTION
# ============================================================================

list_backups() {
    BACKUP_DIR=$(get_backup_dir)
    
    echo ""
    echo "=========================================="
    echo "AVAILABLE BACKUPS"
    echo "=========================================="
    echo ""
    
    if [ ! -d "${BACKUP_DIR}" ]; then
        echo "Backup directory does not exist: ${BACKUP_DIR}"
        return 1
    fi
    
    BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "threads_backup_*.sql.gz" -type f 2>/dev/null | wc -l)
    
    if [ ${BACKUP_COUNT} -eq 0 ]; then
        echo "No backups found in ${BACKUP_DIR}"
        return 0
    fi
    
    echo "Backup directory: ${BACKUP_DIR}"
    echo "Total backups: ${BACKUP_COUNT}"
    echo ""
    echo "Backups:"
    ls -lh "${BACKUP_DIR}"/threads_backup_*.sql.gz 2>/dev/null | awk '{printf "  %-50s %10s\n", $9, $5}'
    
    TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
    echo ""
    echo "Total size: ${TOTAL_SIZE}"
    echo ""
}

# ============================================================================
# MAIN FUNCTION
# ============================================================================

main() {
    # If command provided, run directly
    case "$1" in
        backup)
            mysql_backup
            exit $?
            ;;
        restore)
            restore_backup "$2"
            exit $?
            ;;
        cron)
            setup_cron
            exit $?
            ;;
        list)
            list_backups
            exit $?
            ;;
    esac
    
    # Otherwise show menu
    while true; do
        choice=$(show_menu)
        
        case $choice in
            0)
                echo "👋 Goodbye!"
                exit 0
                ;;
            1)
                mysql_backup
                ;;
            2)
                echo ""
                BACKUP_DIR=$(get_backup_dir)
                echo "Available backups:"
                ls -lh "${BACKUP_DIR}"/threads_backup_*.sql.gz 2>/dev/null | awk '{print NR". "$9, "("$5")"}' || echo "No backups found"
                echo ""
                read -p "Enter backup file path or number: " backup_input
                
                # Check if it's a number
                if [[ "$backup_input" =~ ^[0-9]+$ ]]; then
                    BACKUP_FILE=$(ls -1 "${BACKUP_DIR}"/threads_backup_*.sql.gz 2>/dev/null | sed -n "${backup_input}p")
                else
                    BACKUP_FILE="$backup_input"
                fi
                
                restore_backup "$BACKUP_FILE"
                ;;
            3)
                setup_cron
                ;;
            4)
                list_backups
                ;;
            *)
                echo "❌ Invalid option. Please choose 0-4."
                ;;
        esac
        
        if [ $choice -ne 0 ]; then
            echo ""
            read -p "Press Enter to continue..."
        fi
    done
}

# Run main function
main "$@"
