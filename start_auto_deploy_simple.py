#!/usr/bin/env python3
"""
Простой запуск автоматического деплоя
"""

import os
import sys
import subprocess
import time

def main():
    print("Запускаю автоматический деплой...")
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("Файл .env не найден!")
        print("Скопируйте env_example.txt в .env и заполните настройки:")
        print("   copy env_example.txt .env")
        print("   notepad .env")
        input("Нажмите Enter для продолжения...")
        return
    
    print("Запускаю отслеживание изменений файлов...")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запускаем file_watcher.py
        subprocess.run([sys.executable, "file_watcher.py"])
    except KeyboardInterrupt:
        print("\nАвтоматический деплой остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
