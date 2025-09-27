#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import time

def run_ssh_command(command, description):
    """Выполнение SSH команды"""
    print(f"🔄 {description}...")
    
    # Формируем полную SSH команду
    ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 root@109.172.47.253 "{command}"'
    
    try:
        # Запускаем команду
        process = subprocess.Popen(
            ssh_cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Отправляем пароль
        stdout, stderr = process.communicate(input="MmSS0JSm%6vb\n", timeout=60)
        
        if process.returncode == 0:
            print(f"✅ {description} - успешно")
            if stdout.strip():
                print(f"   Вывод: {stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ошибка")
            print(f"   Код ошибки: {process.returncode}")
            if stderr.strip():
                print(f"   Ошибка: {stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - таймаут")
        process.kill()
        return False
    except Exception as e:
        print(f"💥 {description} - исключение: {e}")
        return False

def main():
    """Простой деплой на сервер"""
    
    print("🚀 Начинаем деплой на сервер 109.172.47.253...")
    print("🔑 Используем пароль: MmSS0JSm%6vb")
    
    # Команды для деплоя
    commands = [
        ("systemctl stop meeting-bot.service || true", "Остановка сервиса"),
        ("rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*", "Очистка места"),
        ("cd /root/b24 && git pull origin main", "Обновление кода"),
        ("""cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF""", "Создание .env файла"),
        ("cd /root/b24 && source venv/bin/activate && pip install -r requirements.txt", "Установка зависимостей"),
        ("""cat > /etc/systemd/system/meeting-bot.service << 'EOF'
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
EOF""", "Обновление systemd сервиса"),
        ("systemctl daemon-reload && systemctl enable meeting-bot.service && systemctl start meeting-bot.service", "Перезапуск сервиса"),
        ("systemctl status meeting-bot.service --no-pager", "Проверка статуса")
    ]
    
    # Выполнение команд
    success_count = 0
    for i, (cmd, desc) in enumerate(commands, 1):
        if run_ssh_command(cmd, f"{desc} (шаг {i}/{len(commands)})"):
            success_count += 1
        else:
            print(f"❌ Деплой прерван на шаге {i}")
            break
    
    # Результат
    if success_count == len(commands):
        print("🎉 Деплой завершен успешно!")
        print("🤖 Бот должен быть запущен на сервере")
        print("📱 Отправьте боту ссылку на встречу для проверки")
    else:
        print(f"⚠️  Деплой завершен частично: {success_count}/{len(commands)} шагов")

if __name__ == "__main__":
    main()
