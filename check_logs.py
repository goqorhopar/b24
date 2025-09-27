#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

def get_last_log_lines(log_file, lines=200):
    """Получить последние строки лога"""
    try:
        if not os.path.exists(log_file):
            return f"Файл лога {log_file} не найден"
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ''.join(last_lines)
    except Exception as e:
        return f"Ошибка чтения лога: {e}"

def main():
    """Основная функция"""
    print("📋 Последние 200 строк логов MCP сервера")
    print("=" * 50)
    
    log_file = "logs/router.log"
    log_content = get_last_log_lines(log_file, 200)
    
    print(log_content)

if __name__ == "__main__":
    main()
