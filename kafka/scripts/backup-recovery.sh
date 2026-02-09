#!/bin/bash
# Kafka Backup and Recovery Procedures
# Scripts for backing up and restoring Kafka data

set -e

# Configuration
KAFKA_HOME="/opt/kafka"
BACKUP_DIR="/backup/kafka"
LOG_FILE="/var/log/kafka-backup.log"
RETENTION_DAYS=7

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Function to backup Kafka data
backup_kafka() {
    log_message "Starting Kafka backup..."
    
    # Create backup directory with timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"
    
    # Stop Kafka (optional, for consistent backup)
    # systemctl stop kafka
    
    # Backup data directory
    if [ -d "/var/lib/kafka/data" ]; then
        tar -czf "$BACKUP_PATH/kafka-data.tar.gz" -C /var/lib/kafka data
        log_message "Data backup completed: $BACKUP_PATH/kafka-data.tar.gz"
    else
        log_message "Warning: Kafka data directory not found"
    fi
    
    # Backup configuration
    if [ -d "/opt/kafka/config" ]; then
        tar -czf "$BACKUP_PATH/kafka-config.tar.gz" -C /opt/kafka config
        log_message "Configuration backup completed: $BACKUP_PATH/kafka-config.tar.gz"
    fi
    
    # Backup topic configurations
    kafka-topics --bootstrap-server localhost:9092 --list | while read topic; do
        kafka-configs --bootstrap-server localhost:9092 --entity-type topics --entity-name "$topic" --describe >> "$BACKUP_PATH/topic-configs.txt"
    done
    
    # Start Kafka (if stopped)
    # systemctl start kafka
    
    log_message "Kafka backup completed successfully"
    
    # Cleanup old backups
    cleanup_old_backups
}

# Function to restore Kafka data
restore_kafka() {
    if [ -z "$1" ]; then
        echo "Usage: $0 restore <backup_timestamp>"
        exit 1
    fi
    
    RESTORE_PATH="$BACKUP_DIR/$1"
    if [ ! -d "$RESTORE_PATH" ]; then
        log_message "Error: Backup path does not exist: $RESTORE_PATH"
        exit 1
    fi
    
    log_message "Starting Kafka restore from: $RESTORE_PATH"
    
    # Stop Kafka
    systemctl stop kafka
    
    # Restore data
    if [ -f "$RESTORE_PATH/kafka-data.tar.gz" ]; then
        rm -rf /var/lib/kafka/data/*
        tar -xzf "$RESTORE_PATH/kafka-data.tar.gz" -C /
        log_message "Data restored from: $RESTORE_PATH/kafka-data.tar.gz"
    fi
    
    # Restore configuration
    if [ -f "$RESTORE_PATH/kafka-config.tar.gz" ]; then
        rm -rf /opt/kafka/config/*
        tar -xzf "$RESTORE_PATH/kafka-config.tar.gz" -C /opt/
        log_message "Configuration restored from: $RESTORE_PATH/kafka-config.tar.gz"
    fi
    
    # Start Kafka
    systemctl start kafka
    
    log_message "Kafka restore completed successfully"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_message "Cleaning up backups older than $RETENTION_DAYS days"
    find $BACKUP_DIR -mindepth 1 -mtime +$RETENTION_DAYS -exec rm -rf {} \;
    log_message "Cleanup completed"
}

# Main script logic
case "$1" in
    backup)
        backup_kafka
        ;;
    restore)
        restore_kafka "$2"
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {backup|restore|cleanup}"
        exit 1
        ;;
esac