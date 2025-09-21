#!/usr/bin/env python3
"""
Автоматический деплой на GitHub и сервер
Система автоматически коммитит изменения и деплоит на сервер
"""

import os
import sys
import subprocess
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoDeployer:
    """Класс для автоматического деплоя"""
    
    def __init__(self):
        self.config = self._load_config()
        self.github_repo = self.config.get('GITHUB_REPO')
        self.github_token = self.config.get('GITHUB_TOKEN')
        self.github_branch = self.config.get('GITHUB_BRANCH', 'main')
        self.deploy_server_url = self.config.get('DEPLOY_SERVER_URL')
        self.deploy_server_user = self.config.get('DEPLOY_SERVER_USER', 'root')
        self.deploy_server_path = self.config.get('DEPLOY_SERVER_PATH', '/opt/meeting-bot')
        self.deploy_restart_command = self.config.get('DEPLOY_RESTART_COMMAND', 'systemctl restart meeting-bot')
        self.telegram_token = self.config.get('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = self.config.get('ADMIN_CHAT_ID')
        
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из .env файла"""
        config = {}
        
        # Загружаем из .env файла
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        # Загружаем из переменных окружения
        for key in [
            'GITHUB_REPO', 'GITHUB_TOKEN', 'GITHUB_BRANCH',
            'DEPLOY_SERVER_URL', 'DEPLOY_SERVER_USER', 'DEPLOY_SERVER_PATH',
            'DEPLOY_RESTART_COMMAND', 'TELEGRAM_BOT_TOKEN', 'ADMIN_CHAT_ID'
        ]:
            if key not in config:
                config[key] = os.getenv(key)
        
        return config
    
    def _run_command(self, command: str, cwd: Optional[str] = None) -> tuple[bool, str]:
        """Выполнение команды"""
        try:
            logger.info(f"Выполняю команду: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Команда выполнена успешно: {command}")
                return True, result.stdout
            else:
                logger.error(f"Ошибка выполнения команды: {command}")
                logger.error(f"Stderr: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"Таймаут выполнения команды: {command}")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"Исключение при выполнении команды: {command}, {e}")
            return False, str(e)
    
    def _send_telegram_notification(self, message: str, is_error: bool = False):
        """Отправка уведомления в Telegram"""
        if not self.telegram_token or not self.admin_chat_id:
            return
        
        try:
            emoji = "❌" if is_error else "✅"
            full_message = f"{emoji} Auto Deploy\n\n{message}"
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.admin_chat_id,
                'text': full_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("Уведомление отправлено в Telegram")
            else:
                logger.error(f"Ошибка отправки в Telegram: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def check_git_status(self) -> bool:
        """Проверка статуса git репозитория"""
        success, output = self._run_command("git status --porcelain")
        if not success:
            logger.error("Ошибка проверки git статуса")
            return False
        
        return len(output.strip()) > 0
    
    def commit_and_push(self, message: str = None) -> bool:
        """Коммит и пуш изменений в GitHub"""
        if not self.github_repo or not self.github_token:
            logger.error("Не настроены GitHub репозиторий или токен")
            return False
        
        # Проверяем есть ли изменения
        if not self.check_git_status():
            logger.info("Нет изменений для коммита")
            return True
        
        # Настраиваем git
        self._run_command(f"git config user.name 'Auto Deployer'")
        self._run_command(f"git config user.email 'auto-deployer@meeting-bot.local'")
        
        # Добавляем все изменения
        success, _ = self._run_command("git add .")
        if not success:
            logger.error("Ошибка добавления файлов в git")
            return False
        
        # Коммит
        if not message:
            message = f"Auto deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success, _ = self._run_command(f'git commit -m "{message}"')
        if not success:
            logger.error("Ошибка коммита")
            return False
        
        # Настраиваем remote с токеном
        remote_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"
        self._run_command(f"git remote set-url origin {remote_url}")
        
        # Пуш
        success, output = self._run_command(f"git push origin {self.github_branch}")
        if not success:
            logger.error(f"Ошибка пуша: {output}")
            return False
        
        logger.info("Изменения успешно отправлены в GitHub")
        return True
    
    def deploy_to_server(self) -> bool:
        """Деплой на сервер"""
        if not self.deploy_server_url or not self.github_repo:
            logger.error("Не настроены параметры сервера или GitHub репозитория")
            return False
        
        try:
            # Команда для деплоя на сервер
            deploy_script = f"""
#!/bin/bash
set -e

echo "🚀 Начинаю деплой на сервер..."

# Переходим в директорию проекта
cd {self.deploy_server_path}

# Останавливаем сервис
echo "⏹️ Останавливаю сервис..."
systemctl stop meeting-bot || true

# Создаем бэкап
echo "💾 Создаю бэкап..."
cp -r . ../meeting-bot-backup-$(date +%Y%m%d-%H%M%S) || true

# Получаем последние изменения
echo "📥 Получаю изменения из GitHub..."
git fetch origin
git reset --hard origin/{self.github_branch}

# Устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
pip3 install -r requirements_simple.txt

# Создаем директории
echo "📁 Создаю необходимые директории..."
mkdir -p /tmp/meeting_bot
mkdir -p logs

# Устанавливаем права
echo "🔐 Устанавливаю права..."
chmod +x start_server_bot.sh
chmod +x *.py

# Запускаем сервис
echo "▶️ Запускаю сервис..."
systemctl start meeting-bot
systemctl enable meeting-bot

# Проверяем статус
echo "✅ Проверяю статус сервиса..."
sleep 5
systemctl status meeting-bot --no-pager

echo "🎉 Деплой завершен успешно!"
"""
            
            # Сохраняем скрипт
            script_path = "/tmp/deploy_script.sh"
            with open(script_path, 'w') as f:
                f.write(deploy_script)
            
            os.chmod(script_path, 0o755)
            
            # Выполняем деплой через SSH
            ssh_command = f"ssh -o StrictHostKeyChecking=no {self.deploy_server_user}@{self.deploy_server_url} 'bash -s' < {script_path}"
            success, output = self._run_command(ssh_command)
            
            # Удаляем временный скрипт
            os.remove(script_path)
            
            if success:
                logger.info("Деплой на сервер выполнен успешно")
                return True
            else:
                logger.error(f"Ошибка деплоя на сервер: {output}")
                return False
                
        except Exception as e:
            logger.error(f"Исключение при деплое на сервер: {e}")
            return False
    
    def full_deploy(self, commit_message: str = None) -> bool:
        """Полный деплой: коммит в GitHub + деплой на сервер"""
        logger.info("🚀 Начинаю полный автоматический деплой...")
        
        # 1. Коммит и пуш в GitHub
        logger.info("📤 Отправляю изменения в GitHub...")
        if not self.commit_and_push(commit_message):
            error_msg = "Ошибка отправки в GitHub"
            logger.error(error_msg)
            self._send_telegram_notification(error_msg, is_error=True)
            return False
        
        # 2. Деплой на сервер
        logger.info("🖥️ Деплою на сервер...")
        if not self.deploy_to_server():
            error_msg = "Ошибка деплоя на сервер"
            logger.error(error_msg)
            self._send_telegram_notification(error_msg, is_error=True)
            return False
        
        # 3. Успешное завершение
        success_msg = f"✅ Деплой завершен успешно!\n\n📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🌿 Ветка: {self.github_branch}\n🖥️ Сервер: {self.deploy_server_url}"
        logger.info("Деплой завершен успешно")
        self._send_telegram_notification(success_msg)
        
        return True
    
    def setup_auto_deploy(self) -> bool:
        """Настройка автоматического деплоя"""
        logger.info("⚙️ Настраиваю автоматический деплой...")
        
        # Проверяем конфигурацию
        required_vars = ['GITHUB_REPO', 'GITHUB_TOKEN', 'DEPLOY_SERVER_URL']
        missing_vars = [var for var in required_vars if not self.config.get(var)]
        
        if missing_vars:
            logger.error(f"Отсутствуют обязательные переменные: {missing_vars}")
            return False
        
        # Создаем GitHub Actions workflow
        workflow_content = f"""name: Auto Deploy

on:
  push:
    branches: [ {self.github_branch} ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{{{ secrets.DEPLOY_SERVER_URL }}}}
        username: ${{{{ secrets.DEPLOY_SERVER_USER }}}}
        key: ${{{{ secrets.DEPLOY_SSH_KEY }}}}
        script: |
          cd {self.deploy_server_path}
          systemctl stop meeting-bot || true
          git fetch origin
          git reset --hard origin/{self.github_branch}
          pip3 install -r requirements_simple.txt
          systemctl start meeting-bot
          systemctl status meeting-bot
"""
        
        # Создаем директорию .github/workflows
        os.makedirs('.github/workflows', exist_ok=True)
        
        # Сохраняем workflow
        with open('.github/workflows/auto-deploy.yml', 'w') as f:
            f.write(workflow_content)
        
        logger.info("GitHub Actions workflow создан")
        
        # Создаем скрипт для быстрого деплоя
        quick_deploy_script = f"""#!/bin/bash
# Быстрый деплой

echo "🚀 Быстрый деплой..."

# Коммит и пуш
python3 auto_deploy.py --commit

# Деплой на сервер
python3 auto_deploy.py --deploy

echo "✅ Деплой завершен!"
"""
        
        with open('quick_deploy.sh', 'w') as f:
            f.write(quick_deploy_script)
        
        os.chmod('quick_deploy.sh', 0o755)
        
        logger.info("Скрипт быстрого деплоя создан")
        
        return True

def main():
    """Главная функция"""
    deployer = AutoDeployer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--commit':
            success = deployer.commit_and_push()
            sys.exit(0 if success else 1)
            
        elif command == '--deploy':
            success = deployer.deploy_to_server()
            sys.exit(0 if success else 1)
            
        elif command == '--setup':
            success = deployer.setup_auto_deploy()
            sys.exit(0 if success else 1)
            
        elif command == '--status':
            has_changes = deployer.check_git_status()
            print(f"Есть изменения: {has_changes}")
            sys.exit(0)
            
        else:
            print("Неизвестная команда")
            sys.exit(1)
    else:
        # Полный деплой
        success = deployer.full_deploy()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()