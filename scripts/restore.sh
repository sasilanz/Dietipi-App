#!/bin/bash

# Database Restore Script for IT-Kurs Application
# This script restores MySQL database from compressed backup files

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-db}"
DB_NAME="${DB_NAME:-itkurs}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_ROOT_PASSWORD}"

# Function to show usage
show_usage() {
    echo "Usage: $0 [backup_file]"
    echo ""
    echo "If no backup file is specified, shows available backups"
    echo ""
    echo "Examples:"
    echo "  $0                                    # List available backups"
    echo "  $0 backup_itkurs_20240901_120000.sql.gz  # Restore specific backup"
    echo "  $0 latest                            # Restore latest backup"
}

# Function to list available backups
list_backups() {
    echo "Available backups in $BACKUP_DIR:"
    if ls -1t "$BACKUP_DIR"/backup_${DB_NAME}_*.sql.gz 2>/dev/null; then
        echo ""
        echo "To restore, run: $0 <backup_filename>"
        echo "To restore latest: $0 latest"
    else
        echo "No backups found!"
        exit 1
    fi
}

# Function to get latest backup
get_latest_backup() {
    ls -1t "$BACKUP_DIR"/backup_${DB_NAME}_*.sql.gz 2>/dev/null | head -1 || {
        echo "No backups found!"
        exit 1
    }
}

# Main logic
if [ $# -eq 0 ]; then
    list_backups
    exit 0
fi

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Determine backup file
if [ "$1" = "latest" ]; then
    BACKUP_FILE=$(get_latest_backup)
    echo "Using latest backup: $(basename "$BACKUP_FILE")"
else
    if [[ "$1" = /* ]]; then
        # Absolute path
        BACKUP_FILE="$1"
    else
        # Relative path or filename
        BACKUP_FILE="$BACKUP_DIR/$1"
    fi
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    echo ""
    list_backups
    exit 1
fi

echo "Starting database restore at $(date)"
echo "Backup file: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Confirm restore (safety measure)
read -p "⚠️  This will REPLACE all data in database '$DB_NAME'. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Perform restore
echo "Restoring database..."
if gunzip -c "$BACKUP_FILE" | mysql \
    --host="$DB_HOST" \
    --user="$DB_USER" \
    --password="$DB_PASSWORD"; then
    
    echo "✅ Database restored successfully from $(basename "$BACKUP_FILE")"
    echo "Restore completed at $(date)"
else
    echo "❌ Restore failed!"
    exit 1
fi
