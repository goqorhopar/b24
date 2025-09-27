#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys

def run_command(cmd, description):
    """Выполнение команды с логированием"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout:
                print(f"   Вывод: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ошибка")
            print(f"   Код ошибки: {result.returncode}")
            if result.stderr:
                print(f"   Ошибка: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - таймаут")
        return False
    except Exception as e:
        print(f"💥 {description} - исключение: {e}")
        return False

def main():
    """Ручной деплой на сервер"""
    
    # Данные сервера (замените на ваши)
    server_host = "109.172.47.253"
    server_user = "root"
    server_password = input("Введите пароль сервера: ")
    
    print("🚀 Начинаем ручной деплой на сервер...")
    
    # Команды для деплоя
    commands = [
        # Остановка сервиса
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "systemctl stop meeting-bot.service || true"',
        
        # Очистка места
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*"',
        
        # Переход в директорию и обновление
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "cd /root/b24 && git pull origin main"',
        
        # Создание .env файла
        f'''sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF"''',
        
        # Установка зависимостей
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "cd /root/b24 && source venv/bin/activate && pip install -r requirements.txt"',
        
        # Обновление systemd сервиса
        f'''sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/b24
ExecStart=/root/b24/venv/bin/python /root/b24/main.py
Restart=always
RestartSec=10
Environment=LOG_LEVEL=INFO
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=USE_POLLING=true
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=BITRIX_USER_ID=1
Environment=DATABASE_URL=sqlite:///bot_state.db

[Install]
WantedBy=multi-user.target
EOF"''',
        
        # Перезапуск сервиса
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "systemctl daemon-reload && systemctl enable meeting-bot.service && systemctl start meeting-bot.service"',
        
        # Проверка статуса
        f'sshpass -p "{server_password}" ssh -o StrictHostKeyChecking=no {server_user}@{server_host} "systemctl status meeting-bot.service --no-pager"'
    ]
    
    # Выполнение команд
    success_count = 0
    for i, cmd in enumerate(commands, 1):
        if run_command(cmd, f"Шаг {i}/{len(commands)}"):
            success_count += 1
        else:
            print(f"❌ Деплой прерван на шаге {i}")
            break
    
    if success_count == len(commands):
        print("🎉 Деплой завершен успешно!")
        print("🤖 Бот должен быть запущен на сервере")
    else:
        print(f"⚠️  Деплой завершен частично: {success_count}/{len(commands)} шагов")

if __name__ == "__main__":
    main()
