#!/bin/bash

# Скрипт для создания бэкапа старых данных и очистки

set -e

# Конфигурация
BACKUP_DIR="/opt/meetingbot/backups"
DATA_DIR="/data/meetingbot"
LOGS_DIR="/var/log/meetingbot"
RETENTION_DAYS=7
MAX_BACKUP_SIZE="1G"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Функция создания бэкапа
create_backup() {
    local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
    local backup_file="$BACKUP_DIR/$backup_name.tar.gz"
    
    log "Creating backup: $backup_name"
    
    # Создание директории для бэкапов
    mkdir -p "$BACKUP_DIR"
    
    # Создание бэкапа
    tar -czf "$backup_file" \
        --exclude="*.tmp" \
        --exclude="*.log" \
        --exclude="node_modules" \
        --exclude=".git" \
        "$DATA_DIR" "$LOGS_DIR" 2>/dev/null || {
        error "Failed to create backup"
        return 1
    }
    
    # Проверка размера бэкапа
    local backup_size=$(du -h "$backup_file" | cut -f1)
    log "Backup created: $backup_file (Size: $backup_size)"
    
    # Проверка максимального размера
    if [ -n "$MAX_BACKUP_SIZE" ]; then
        local size_bytes=$(du -b "$backup_file" | cut -f1)
        local max_bytes=$(numfmt --from=iec "$MAX_BACKUP_SIZE")
        
        if [ "$size_bytes" -gt "$max_bytes" ]; then
            warn "Backup size ($backup_size) exceeds maximum size ($MAX_BACKUP_SIZE)"
        fi
    fi
    
    echo "$backup_file"
}

# Функция очистки старых бэкапов
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)"
    
    local deleted_count=0
    
    # Удаление старых бэкапов
    while IFS= read -r -d '' file; do
        log "Deleting old backup: $(basename "$file")"
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [ $deleted_count -eq 0 ]; then
        log "No old backups to delete"
    else
        log "Deleted $deleted_count old backup(s)"
    fi
}

# Функция очистки старых логов
cleanup_old_logs() {
    log "Cleaning up old log files"
    
    local deleted_count=0
    
    # Очистка логов старше 7 дней
    while IFS= read -r -d '' file; do
        log "Deleting old log: $(basename "$file")"
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$LOGS_DIR" -name "*.log" -mtime +7 -print0 2>/dev/null)
    
    if [ $deleted_count -eq 0 ]; then
        log "No old logs to delete"
    else
        log "Deleted $deleted_count old log file(s)"
    fi
}

# Функция очистки временных файлов
cleanup_temp_files() {
    log "Cleaning up temporary files"
    
    local deleted_count=0
    
    # Очистка временных файлов
    while IFS= read -r -d '' file; do
        log "Deleting temp file: $(basename "$file")"
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$DATA_DIR" -name "*.tmp" -mtime +1 -print0 2>/dev/null)
    
    if [ $deleted_count -eq 0 ]; then
        log "No temporary files to delete"
    else
        log "Deleted $deleted_count temporary file(s)"
    fi
}

# Функция проверки дискового пространства
check_disk_space() {
    local data_dir_usage=$(df -h "$DATA_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    local logs_dir_usage=$(df -h "$LOGS_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    log "Disk usage - Data: ${data_dir_usage}%, Logs: ${logs_dir_usage}%"
    
    if [ "$data_dir_usage" -gt 80 ]; then
        warn "Data directory disk usage is high: ${data_dir_usage}%"
    fi
    
    if [ "$logs_dir_usage" -gt 80 ]; then
        warn "Logs directory disk usage is high: ${logs_dir_usage}%"
    fi
}

# Функция сжатия старых аудио файлов
compress_old_audio() {
    log "Compressing old audio files"
    
    local compressed_count=0
    
    # Поиск аудио файлов старше 3 дней
    while IFS= read -r -d '' file; do
        if [[ "$file" =~ \.(wav|flac)$ ]]; then
            local compressed_file="${file%.*}.mp3"
            
            # Сжатие в MP3 если файл больше 10MB
            if [ $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null) -gt 10485760 ]; then
                log "Compressing: $(basename "$file")"
                
                if command -v ffmpeg >/dev/null 2>&1; then
                    ffmpeg -i "$file" -acodec mp3 -ab 128k "$compressed_file" -y 2>/dev/null && {
                        rm -f "$file"
                        ((compressed_count++))
                    }
                fi
            fi
        fi
    done < <(find "$DATA_DIR" -name "*.wav" -o -name "*.flac" -mtime +3 -print0 2>/dev/null)
    
    if [ $compressed_count -eq 0 ]; then
        log "No audio files to compress"
    else
        log "Compressed $compressed_count audio file(s)"
    fi
}

# Функция ротации логов
rotate_logs() {
    log "Rotating log files"
    
    # Ротация логов если они больше 100MB
    find "$LOGS_DIR" -name "*.log" -size +100M -exec sh -c '
        for file; do
            mv "$file" "${file}.$(date +%Y%m%d-%H%M%S)"
            touch "$file"
            log "Rotated log file: $(basename "$file")"
        done
    ' sh {} +
}

# Функция проверки целостности данных
check_data_integrity() {
    log "Checking data integrity"
    
    local errors=0
    
    # Проверка базы данных
    if [ -f "$DATA_DIR/meetingbot.db" ]; then
        if command -v sqlite3 >/dev/null 2>&1; then
            if ! sqlite3 "$DATA_DIR/meetingbot.db" "PRAGMA integrity_check;" >/dev/null 2>&1; then
                error "Database integrity check failed"
                ((errors++))
            else
                log "Database integrity check passed"
            fi
        fi
    fi
    
    # Проверка аудио файлов
    local corrupted_audio=0
    while IFS= read -r -d '' file; do
        if command -v ffprobe >/dev/null 2>&1; then
            if ! ffprobe -v quiet -show_error "$file" >/dev/null 2>&1; then
                warn "Corrupted audio file detected: $(basename "$file")"
                ((corrupted_audio++))
            fi
        fi
    done < <(find "$DATA_DIR" -name "*.wav" -o -name "*.mp3" -print0 2>/dev/null)
    
    if [ $corrupted_audio -gt 0 ]; then
        warn "Found $corrupted_audio corrupted audio file(s)"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log "Data integrity check passed"
    else
        error "Data integrity check found $errors issue(s)"
    fi
    
    return $errors
}

# Основная функция
main() {
    log "Starting backup and cleanup process"
    
    # Проверка прав доступа
    if [ ! -w "$DATA_DIR" ] || [ ! -w "$LOGS_DIR" ]; then
        error "Insufficient permissions to access data or logs directories"
        exit 1
    fi
    
    # Создание бэкапа
    create_backup
    
    # Очистка старых данных
    cleanup_old_backups
    cleanup_old_logs
    cleanup_temp_files
    
    # Сжатие аудио файлов
    compress_old_audio
    
    # Ротация логов
    rotate_logs
    
    # Проверка дискового пространства
    check_disk_space
    
    # Проверка целостности данных
    check_data_integrity
    
    log "Backup and cleanup process completed successfully"
}

# Обработка аргументов командной строки
case "${1:-}" in
    --backup-only)
        log "Creating backup only"
        create_backup
        ;;
    --cleanup-only)
        log "Running cleanup only"
        cleanup_old_backups
        cleanup_old_logs
        cleanup_temp_files
        compress_old_audio
        rotate_logs
        ;;
    --check-only)
        log "Running checks only"
        check_disk_space
        check_data_integrity
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --backup-only    Create backup only"
        echo "  --cleanup-only   Run cleanup only"
        echo "  --check-only     Run checks only"
        echo "  --help          Show this help"
        echo ""
        echo "Default: Run full backup and cleanup process"
        exit 0
        ;;
    *)
        main
        ;;
esac
