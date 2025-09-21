#!/usr/bin/env python3
"""
Простая настройка автоматического деплоя для Windows
"""

import os
import sys
import subprocess

def run_command(command: str) -> tuple[bool, str]:
    """Выполнение команды"""
    try:
        print(f"Выполняю: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"Успешно: {command}")
            return True, result.stdout
        else:
            print(f"Ошибка: {command}")
            print(f"   {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"Исключение: {command}, {e}")
        return False, str(e)

def setup_git_hooks():
    """Настройка Git hooks для автоматического деплоя"""
    print("Настраиваю Git hooks...")
    
    # Создаем директорию hooks если не существует
    hooks_dir = ".git/hooks"
    if not os.path.exists(hooks_dir):
        print("Директория .git/hooks не найдена!")
        return False
    
    # Pre-push hook для автоматического деплоя
    pre_push_hook = """#!/bin/bash
# Pre-push hook для автоматического деплоя

echo "Pre-push hook: Проверяю изменения..."

# Проверяем есть ли изменения
if git diff --quiet HEAD~1 HEAD; then
    echo "Нет изменений для деплоя"
    exit 0
fi

echo "Есть изменения, запускаю автоматический деплой..."

# Запускаем автоматический деплой
python auto_deploy.py --commit

if [ $? -eq 0 ]; then
    echo "Автоматический деплой выполнен успешно"
else
    echo "Ошибка автоматического деплоя"
    exit 1
fi
"""
    
    # Сохраняем pre-push hook
    with open(f"{hooks_dir}/pre-push", 'w', encoding='utf-8') as f:
        f.write(pre_push_hook)
    
    print("Pre-push hook настроен")
    
    return True

def setup_auto_commit():
    """Настройка автоматического коммита"""
    print("Настраиваю автоматический коммит...")
    
    # Создаем скрипт для автоматического коммита
    auto_commit_script = """#!/bin/bash
# Автоматический коммит изменений

echo "Автоматический коммит..."

# Проверяем есть ли изменения
if git diff --quiet && git diff --cached --quiet; then
    echo "Нет изменений для коммита"
    exit 0
fi

# Добавляем все изменения
git add .

# Создаем коммит с текущим временем
commit_message="Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_message"

if [ $? -eq 0 ]; then
    echo "Автоматический коммит выполнен: $commit_message"
    
    # Запускаем автоматический деплой
    python auto_deploy.py --commit
    
    if [ $? -eq 0 ]; then
        echo "Автоматический деплой выполнен"
    else
        echo "Ошибка автоматического деплоя"
    fi
else
    echo "Ошибка автоматического коммита"
    exit 1
fi
"""
    
    # Сохраняем скрипт
    with open('auto_commit.sh', 'w', encoding='utf-8') as f:
        f.write(auto_commit_script)
    
    print("Скрипт автоматического коммита создан: auto_commit.sh")
    
    return True

def setup_file_watcher():
    """Настройка отслеживания изменений файлов"""
    print("Настраиваю отслеживание изменений файлов...")
    
    # Создаем скрипт для отслеживания изменений
    file_watcher_script = """#!/usr/bin/env python3
# Отслеживание изменений файлов и автоматический коммит

import os
import time
import subprocess
from datetime import datetime

def run_command(command: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def check_changes():
    success, _ = run_command("git diff --quiet")
    if success:
        success, _ = run_command("git diff --cached --quiet")
        if success:
            return False
    return True

def auto_commit():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Обнаружены изменения, создаю коммит...")
    
    success, output = run_command("git add .")
    if not success:
        print(f"Ошибка добавления файлов: {output}")
        return False
    
    commit_message = f"Auto commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(f'git commit -m "{commit_message}"')
    
    if not success:
        print(f"Ошибка коммита: {output}")
        return False
    
    print(f"Коммит создан: {commit_message}")
    
    success, output = run_command("python auto_deploy.py --commit")
    
    if success:
        print("Автоматический деплой выполнен")
        return True
    else:
        print(f"Ошибка деплоя: {output}")
        return False

def main():
    print("Запускаю отслеживание изменений файлов...")
    print("Для остановки нажмите Ctrl+C")
    
    last_check = 0
    check_interval = 10
    
    try:
        while True:
            current_time = time.time()
            
            if current_time - last_check >= check_interval:
                if check_changes():
                    auto_commit()
                last_check = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Отслеживание остановлено")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
"""
    
    # Сохраняем скрипт
    with open('file_watcher.py', 'w', encoding='utf-8') as f:
        f.write(file_watcher_script)
    
    print("Скрипт отслеживания файлов создан: file_watcher.py")
    
    return True

def setup_github_actions():
    """Настройка GitHub Actions для автоматического деплоя"""
    print("Настраиваю GitHub Actions...")
    
    # Создаем директорию .github/workflows если не существует
    os.makedirs('.github/workflows', exist_ok=True)
    
    # Проверяем есть ли уже workflow
    if os.path.exists('.github/workflows/auto-deploy.yml'):
        print("GitHub Actions workflow уже существует")
        return True
    
    print("Создайте GitHub Actions workflow вручную")
    print("   Файл: .github/workflows/auto-deploy.yml")
    
    return True

def create_startup_script():
    """Создание скрипта для запуска автоматического деплоя"""
    print("Создаю скрипт запуска...")
    
    startup_script = """#!/bin/bash
# Запуск автоматического деплоя

echo "Запускаю автоматический деплой..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "Файл .env не найден!"
    echo "Скопируйте env_example.txt в .env и заполните настройки:"
    echo "   cp env_example.txt .env"
    echo "   nano .env"
    exit 1
fi

# Запускаем отслеживание файлов в фоне
echo "Запускаю отслеживание изменений файлов..."
python file_watcher.py &

# Сохраняем PID процесса
echo $! > file_watcher.pid

echo "Автоматический деплой запущен"
echo "PID процесса отслеживания: $(cat file_watcher.pid)"
echo "Для остановки: kill $(cat file_watcher.pid)"
"""
    
    # Сохраняем скрипт
    with open('start_auto_deploy.sh', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("Скрипт запуска создан: start_auto_deploy.sh")
    
    return True

def main():
    """Главная функция"""
    print("НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ ДЛЯ ЛОКАЛЬНОГО РЕПОЗИТОРИЯ")
    print("=" * 60)
    
    try:
        # 1. Настраиваем Git hooks
        if not setup_git_hooks():
            print("Ошибка настройки Git hooks!")
            return False
        
        # 2. Настраиваем автоматический коммит
        if not setup_auto_commit():
            print("Ошибка настройки автоматического коммита!")
            return False
        
        # 3. Настраиваем отслеживание файлов
        if not setup_file_watcher():
            print("Ошибка настройки отслеживания файлов!")
            return False
        
        # 4. Настраиваем GitHub Actions
        setup_github_actions()
        
        # 5. Создаем скрипт запуска
        if not create_startup_script():
            print("Ошибка создания скрипта запуска!")
            return False
        
        print("\n" + "=" * 60)
        print("НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print("\nЧто было настроено:")
        print("   - Git hooks для автоматического деплоя")
        print("   - Скрипт автоматического коммита")
        print("   - Отслеживание изменений файлов")
        print("   - Скрипт запуска")
        print("\nКак использовать:")
        print("   1. Заполните .env файл")
        print("   2. Запустите: start_auto_deploy.bat")
        print("   3. Любые изменения автоматически коммитятся и деплоятся!")
        print("\nДля остановки:")
        print("   Закройте окно start_auto_deploy.bat")
        
        return True
        
    except Exception as e:
        print(f"Ошибка настройки: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
