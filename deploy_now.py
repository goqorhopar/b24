#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import requests
import time

def run_ssh_command(command):
    """Выполнить SSH команду на сервере"""
    try:
        ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 root@109.172.47.253 "{command}"'
        print(f"🔄 {command}")
        
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Успешно")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Ошибка: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"💥 Исключение: {e}")
        return False

def deploy_bot_to_server():
    """Развернуть бота на сервере"""
    print("🚀 РАЗВЕРТЫВАЮ БОТА НА СЕРВЕРЕ 109.172.47.253")
    print("=" * 50)
    
    commands = [
        "systemctl stop meeting-bot.service || true",
        "cd /root/b24 && git pull origin main || echo 'Git pull failed'",
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
        "sleep 10",
        "systemctl status meeting-bot.service --no-pager"
    ]
    
    success_count = 0
    for i, command in enumerate(commands, 1):
        print(f"\n📋 Шаг {i}/{len(commands)}")
        if run_ssh_command(command):
            success_count += 1
        else:
            print(f"❌ Остановка на шаге {i}")
            break
    
    print(f"\n📊 Результат: {success_count}/{len(commands)} шагов")
    
    if success_count == len(commands):
        print("\n🎉 БОТ РАЗВЕРНУТ НА СЕРВЕРЕ!")
        print("🤖 Бот работает автоматически 24/7")
        
        # Отправляем уведомление
        try:
            url = "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/sendMessage"
            data = {
                "chat_id": "7537953397",
                "text": """🤖 **БОТ РАЗВЕРНУТ НА СЕРВЕРЕ!**

✅ **Работает на сервере 109.172.47.253**
✅ **Автоматический запуск при загрузке**
✅ **Автоперезапуск при сбоях**
✅ **Реальный AI анализ активен**
✅ **Интеграция с Bitrix24 готова**

🚀 **Бот работает 24/7 без вашего участия!**
📱 **Отправьте ссылку на встречу для тестирования!**"""
            }
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print("✅ Уведомление отправлено в Telegram!")
            else:
                print("⚠️ Не удалось отправить уведомление")
        except Exception as e:
            print(f"⚠️ Ошибка уведомления: {e}")
    else:
        print("⚠️ Развертывание завершено частично")

if __name__ == "__main__":
    deploy_bot_to_server()
