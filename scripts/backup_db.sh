#!/bin/bash
# Backup databases for AI News Parser

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Backup directory
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}Starting database backup...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup main database
if [ -f "$PROJECT_ROOT/data/ainews.db" ]; then
    echo -e "${YELLOW}Backing up main database...${NC}"
    cp "$PROJECT_ROOT/data/ainews.db" "$BACKUP_DIR/ainews_${TIMESTAMP}.db"
    echo "✓ Main database backed up"
fi

# Backup monitoring database
if [ -f "$PROJECT_ROOT/data/monitoring.db" ]; then
    echo -e "${YELLOW}Backing up monitoring database...${NC}"
    cp "$PROJECT_ROOT/data/monitoring.db" "$BACKUP_DIR/monitoring_${TIMESTAMP}.db"
    echo "✓ Monitoring database backed up"
fi

# Remove old backups (keep last 10)
echo -e "${YELLOW}Cleaning old backups...${NC}"
cd "$BACKUP_DIR"
ls -t ainews_*.db 2>/dev/null | tail -n +11 | xargs -r rm
ls -t monitoring_*.db 2>/dev/null | tail -n +11 | xargs -r rm

echo -e "${GREEN}Backup completed successfully!${NC}"
echo "Backups stored in: $BACKUP_DIR"