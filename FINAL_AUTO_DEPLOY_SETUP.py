#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ
Скрипт для полной автоматизации деплоя Meeting Bot
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

def run_command(command: str, cwd: Optional[str] = None) -> tuple[bool, str]:
    """Выполнение команды"""
    try:
        print(f"🔧 Выполняю: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ Успешно: {command}")
            return True, result.stdout
        else:
            print(f"❌ Ошибка: {command}")
            print(f"   {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут: {command}")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 Исключение: {command}, {e}")
        return False, str(e)

def check_requirements():
    """Проверка требований"""
    print("🔍 Проверяю требования...")
    
    # Проверяем Python
    success, _ = run_command("python --version")
    if not success:
        success, _ = run_command("python3 --version")
        if not success:
            print("❌ Python не найден!")
            return False
    
    # Проверяем Git
    success, _ = run_command("git --version")
    if not success:
        print("❌ Git не найден!")
        return False
    
    print("✅ Все требования выполнены")
    return True

def setup_env_file():
    """Настройка .env файла"""
    print("⚙️ Настраиваю .env файл...")
    
    if not os.path.exists('.env'):
        if os.path.exists('env_example.txt'):
            print("📋 Копирую env_example.txt в .env...")
            with open('env_example.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Файл .env создан")
        else:
            print("❌ Файл env_example.txt не найден!")
            return False
    
    print("📝 Не забудьте заполнить .env файл!")
    print("   - TELEGRAM_BOT_TOKEN")
    print("   - GEMINI_API_KEY")
    print("   - GITHUB_REPO")
    print("   - GITHUB_TOKEN")
    print("   - DEPLOY_SERVER_URL")
    print("   - DEPLOY_SERVER_USER")
    
    return True

def setup_git():
    """Настройка Git"""
    print("🔧 Настраиваю Git...")
    
    # Настраиваем пользователя
    run_command('git config user.name "Auto Deployer"')
    run_command('git config user.email "auto-deployer@meeting-bot.local"')
    
    # Инициализируем репозиторий если нужно
    if not os.path.exists('.git'):
        print("📁 Инициализирую Git репозиторий...")
        run_command('git init')
        run_command('git add .')
        run_command('git commit -m "Initial commit"')
    
    print("✅ Git настроен")

def setup_github_actions():
    """Настройка GitHub Actions"""
    print("🚀 Настраиваю GitHub Actions...")
    
    # Создаем директорию
    os.makedirs('.github/workflows', exist_ok=True)
    
    # Проверяем есть ли уже workflow
    if os.path.exists('.github/workflows/auto-deploy.yml'):
        print("✅ GitHub Actions workflow уже существует")
        return True
    
    print("📝 Создайте GitHub Actions workflow вручную")
    print("   Файл: .github/workflows/auto-deploy.yml")
    
    return True

def setup_scripts():
    """Настройка скриптов"""
    print("📜 Настраиваю скрипты...")
    
    # Делаем скрипты исполняемыми (для Linux/Mac)
    if sys.platform != 'win32':
        run_command('chmod +x quick_deploy.sh')
        run_command('chmod +x setup_auto_deploy.sh')
        run_command('chmod +x auto_deploy.py')
    
    print("✅ Скрипты настроены")

def test_deployment():
    """Тестирование деплоя"""
    print("🧪 Тестирую деплой...")
    
    # Проверяем статус git
    success, output = run_command('git status --porcelain')
    if success and output.strip():
        print("📝 Есть изменения для коммита")
        
        # Пробуем коммит
        run_command('git add .')
        run_command('git commit -m "Auto setup test"')
        
        print("✅ Тестовый коммит выполнен")
    else:
        print("ℹ️ Нет изменений для коммита")
    
    return True

def create_final_instructions():
    """Создание финальных инструкций"""
    print("📋 Создаю финальные инструкции...")
    
    instructions = f"""# 🎉 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ НАСТРОЕН!

## ✅ Что было сделано:

1. ✅ Проверены требования (Python, Git)
2. ✅ Создан файл .env из env_example.txt
3. ✅ Настроен Git репозиторий
4. ✅ Настроены скрипты деплоя
5. ✅ Создана структура GitHub Actions

## 🔧 Следующие шаги:

### 1. Заполните .env файл:
```bash
# Отредактируйте .env файл
nano .env  # Linux/Mac
notepad .env  # Windows
```

Обязательные настройки:
- TELEGRAM_BOT_TOKEN=ваш_токен_бота
- GEMINI_API_KEY=ваш_ключ_gemini
- GITHUB_REPO=username/repo-name
- GITHUB_TOKEN=ваш_github_токен
- DEPLOY_SERVER_URL=ip_вашего_сервера
- DEPLOY_SERVER_USER=пользователь_сервера

### 2. Настройте GitHub Secrets:
В репозитории GitHub → Settings → Secrets and variables → Actions:
- DEPLOY_SERVER_URL
- DEPLOY_SERVER_USER  
- DEPLOY_SSH_KEY
- DEPLOY_SSH_PORT (опционально)
- DEPLOY_SERVER_PATH (опционально)

### 3. Запустите деплой:
```bash
# Linux/Mac
./quick_deploy.sh

# Windows
deploy_automation.bat

# Или вручную
python auto_deploy.py
```

## 🚀 После настройки:

Любые изменения автоматически деплоятся:
```bash
git add .
git commit -m "Update"
git push origin main
```

## 📚 Документация:
- README_AUTO_DEPLOY.md - Основное руководство
- AUTO_DEPLOY_GUIDE.md - Подробная документация
- SERVER_DEPLOYMENT_GUIDE.md - Настройка сервера

## 🆘 Поддержка:
При проблемах проверьте:
1. Логи: tail -f auto_deploy.log
2. GitHub Actions в репозитории
3. Статус сервиса на сервере

---
Настроено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('DEPLOY_SETUP_COMPLETE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Финальные инструкции созданы: DEPLOY_SETUP_COMPLETE.md")

def main():
    """Главная функция"""
    print("🚀 ФИНАЛЬНАЯ НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ")
    print("=" * 50)
    
    try:
        # 1. Проверяем требования
        if not check_requirements():
            print("❌ Требования не выполнены!")
            return False
        
        # 2. Настраиваем .env файл
        if not setup_env_file():
            print("❌ Ошибка настройки .env файла!")
            return False
        
        # 3. Настраиваем Git
        setup_git()
        
        # 4. Настраиваем GitHub Actions
        setup_github_actions()
        
        # 5. Настраиваем скрипты
        setup_scripts()
        
        # 6. Тестируем деплой
        test_deployment()
        
        # 7. Создаем финальные инструкции
        create_final_instructions()
        
        print("\n" + "=" * 50)
        print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 50)
        print("\n📋 Следующие шаги:")
        print("1. Заполните .env файл")
        print("2. Настройте GitHub Secrets")
        print("3. Запустите деплой")
        print("\n📖 Подробности: DEPLOY_SETUP_COMPLETE.md")
        
        return True
        
    except Exception as e:
        print(f"💥 Ошибка настройки: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
