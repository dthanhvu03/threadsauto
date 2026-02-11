#!/bin/bash
#
# Unified Shell Scripts for Threads Automation Tool
# Combines all shell scripts into one with menu
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"


# ============================================================================
# MENU FUNCTIONS
# ============================================================================

show_menu() {
    echo ""
    echo "=========================================="
    echo "SHELL SCRIPTS MENU"
    echo "=========================================="
    echo ""
    echo "1. Backup Jobs"
    echo "2. Docker MySQL Setup"
    echo ""
    echo "0. Exit"
    echo ""
    read -p "Chọn option (0-2): " choice
    echo "$choice"
}


# ============================================================================
# BACKUP JOBS
# ============================================================================

backup_jobs() {
    echo ""
    echo "=========================================="
    echo "📦 BACKUP JOBS DIRECTORY"
    echo "=========================================="
    echo ""
    
    JOBS_DIR="$PROJECT_ROOT/jobs"
    BACKUP_DIR="$PROJECT_ROOT/backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/jobs_backup_$TIMESTAMP.tar.gz"
    
    # Create backup directory if not exists
    mkdir -p "$BACKUP_DIR"
    
    echo "📦 Creating backup of jobs directory..."
    echo "   Source: $JOBS_DIR"
    echo "   Backup: $BACKUP_FILE"
    echo ""
    
    # Create tar.gz backup
    if [ -d "$JOBS_DIR" ]; then
        tar -czf "$BACKUP_FILE" -C "$PROJECT_ROOT" jobs/
        
        # Get backup size
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        
        echo -e "${GREEN}✅ Backup created successfully!${NC}"
        echo "   File: $BACKUP_FILE"
        echo "   Size: $BACKUP_SIZE"
        echo ""
        echo "📋 Backup location: $BACKUP_FILE"
    else
        echo -e "${RED}⚠️  Jobs directory not found: $JOBS_DIR${NC}"
        return 1
    fi
    
    # List recent backups
    echo ""
    echo "📚 Recent backups:"
    ls -lh "$BACKUP_DIR"/jobs_backup_*.tar.gz 2>/dev/null | tail -5 | awk '{print "   " $9 " (" $5 ")"}'
    echo ""
}


# ============================================================================
# DOCKER MYSQL SETUP
# ============================================================================

docker_mysql_setup() {
    echo ""
    echo "=========================================="
    echo "🐳 DOCKER MYSQL SETUP"
    echo "=========================================="
    echo ""
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"
    echo ""
    
    # Check .env file
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}✅ Created .env file${NC}"
            echo -e "${YELLOW}⚠️  Please edit .env file with your credentials before continuing${NC}"
            echo ""
        else
            echo -e "${RED}❌ .env.example not found. Please create .env manually.${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ .env file exists${NC}"
    fi
    
    # Check docker-compose.yml
    if [ ! -f docker-compose.yml ]; then
        echo -e "${RED}❌ docker-compose.yml not found${NC}"
        return 1
    fi
    
    echo ""
    echo "Starting MySQL container..."
    echo ""
    
    # Start MySQL
    docker-compose up -d mysql
    
    # Wait for MySQL to be ready
    echo ""
    echo "Waiting for MySQL to be ready..."
    sleep 5
    
    # Check if container is running
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ MySQL container is running${NC}"
    else
        echo -e "${RED}❌ MySQL container failed to start${NC}"
        echo "Check logs with: docker-compose logs mysql"
        return 1
    fi
    
    # Wait for healthcheck
    echo ""
    echo "Waiting for MySQL to be healthy..."
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if docker-compose ps | grep -q "healthy"; then
            echo -e "${GREEN}✅ MySQL is healthy${NC}"
            break
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -n "."
    done
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}❌ MySQL healthcheck timeout${NC}"
        echo "Check logs with: docker-compose logs mysql"
        return 1
    fi
    
    # Verify schema
    echo ""
    echo "Verifying database schema..."
    sleep 2
    
    # Load .env variables
    source .env
    
    DB_USER=${MYSQL_USER:-threads_user}
    DB_NAME=${MYSQL_DATABASE:-threads_analytics}
    
    TABLES=$(docker-compose exec -T mysql mysql -u "$DB_USER" -p"${MYSQL_PASSWORD:-threads_password}" "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)
    
    if [ "$TABLES" -gt 1 ]; then
        echo -e "${GREEN}✅ Database schema verified (found $((TABLES-1)) tables)${NC}"
    else
        echo -e "${YELLOW}⚠️  Schema may not be initialized. Check logs.${NC}"
    fi
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo ""
    echo "MySQL is running at:"
    echo "  - Host: localhost"
    echo "  - Port: ${MYSQL_PORT:-3306}"
    echo "  - Database: $DB_NAME"
    echo "  - User: $DB_USER"
    echo ""
    echo "Useful commands:"
    echo "  - View logs: docker-compose logs -f mysql"
    echo "  - Stop: docker-compose stop mysql"
    echo "  - Start: docker-compose up -d mysql"
    echo "  - Access MySQL: docker-compose exec mysql mysql -u $DB_USER -p $DB_NAME"
    echo ""
    if docker-compose ps | grep -q "phpmyadmin"; then
        echo "phpMyAdmin available at: http://localhost:${PHPMYADMIN_PORT:-8080}"
    fi
    echo ""
}


# ============================================================================
# MAIN FUNCTION
# ============================================================================

main() {
    # Check for command line arguments
    if [ "$#" -gt 0 ]; then
        case "$1" in
            "backup-jobs"|"backup")
                backup_jobs
                exit $?
                ;;
            "docker-mysql"|"mysql")
                docker_mysql_setup
                exit $?
                ;;
            *)
                echo "Usage: $0 [backup-jobs|docker-mysql]"
                echo ""
                echo "Commands:"
                echo "  backup-jobs, backup    - Backup jobs directory"
                echo "  docker-mysql, mysql    - Setup Docker MySQL"
                echo ""
                echo "Or run without arguments for interactive menu"
                exit 1
                ;;
        esac
    fi
    
    # Interactive menu
    while true; do
        choice=$(show_menu)
        
        case "$choice" in
            "0")
                echo "👋 Goodbye!"
                exit 0
                ;;
            "1")
                backup_jobs
                ;;
            "2")
                docker_mysql_setup
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please choose 0-2.${NC}"
                ;;
        esac
        
        if [ "$choice" != "0" ]; then
            echo ""
            read -p "Press Enter to continue..."
        fi
    done
}


# Run main function
main "$@"
