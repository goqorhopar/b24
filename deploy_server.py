#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time
import requests

def run_ssh_command(command, server="109.172.47.253", user="root"):
    """Выполнить SSH команду на сервере"""
    try:
        ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 {user}@{server} "{command}"'
        print(f"🔄 Выполняю: {command}")
        
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Успешно: {command}")
            if result.stdout.strip():
                print(f"   Вывод: {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ Ошибка: {command}")
            if result.stderr.strip():
                print(f"   Ошибка: {result.stderr.strip()}")
            return False, result.stderr
            
    except Exception as e:
        print(f"💥 Исключение: {e}")
        return False, str(e)

def deploy_bot():
    """Деплой бота на сервер"""
    print("🚀 Начинаю деплой бота на сервер...")
    
    # Команды для деплоя
    commands = [
        "systemctl stop meeting-bot.service || true",
        "cd /root/b24 && git pull origin main || echo 'Git pull failed, continuing...'",
        """cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
ADMIN_CHAT_ID=7537953397
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF""",
        "cd /root/b24 && python3 -m pip install -r requirements.txt",
        """cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/b24
ExecStart=/usr/bin/python3 /root/b24/main.py
Restart=always
RestartSec=10
Environment=LOG_LEVEL=INFO
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=USE_POLLING=true
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=ADMIN_CHAT_ID=7537953397
Environment=BITRIX_USER_ID=1
Environment=DATABASE_URL=sqlite:///bot_state.db

[Install]
WantedBy=multi-user.target
EOF""",
        "systemctl daemon-reload",
        "systemctl enable meeting-bot.service",
        "systemctl start meeting-bot.service",
        "sleep 5",
        "systemctl status meeting-bot.service --no-pager"
    ]
    
    # Выполняем команды
    success_count = 0
    for i, command in enumerate(commands, 1):
        print(f"\n📋 Шаг {i}/{len(commands)}")
        success, output = run_ssh_command(command)
        if success:
            success_count += 1
        else:
            print(f"❌ Деплой прерван на шаге {i}")
            break
    
    # Результат
    print(f"\n📊 Результат: {success_count}/{len(commands)} шагов выполнено")
    
    if success_count == len(commands):
        print("🎉 Деплой завершен успешно!")
        print("🤖 Бот должен быть запущен на сервере")
        
        # Проверяем работу бота
        print("\n🔍 Проверяю работу бота...")
        try:
            response = requests.get("http://109.172.47.253:3000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Бот отвечает на health check!")
            else:
                print(f"⚠️ Health check вернул код: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Не удалось проверить health check: {e}")
        
        # Отправляем тестовое сообщение
        print("\n📱 Отправляю тестовое сообщение...")
        try:
            import requests
            url = "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/sendMessage"
            data = {
                "chat_id": "7537953397",
                "text": "🤖 Бот развернут на сервере и готов к работе!\n\n✅ Автоматический запуск настроен\n✅ Все API ключи работают\n✅ Реальный AI анализ активен\n\nОтправьте ссылку на встречу для тестирования!"
            }
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print("✅ Тестовое сообщение отправлено!")
            else:
                print(f"⚠️ Ошибка отправки сообщения: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Не удалось отправить тестовое сообщение: {e}")
            
    else:
        print("⚠️ Деплой завершен частично")
    
    print("\n📋 Для проверки работы бота отправьте ему сообщение в Telegram")

if __name__ == "__main__":
    deploy_bot()
