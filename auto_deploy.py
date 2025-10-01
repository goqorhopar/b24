#!/usr/bin/env python3
"""
Автоматический деплой Meeting Bot на сервер
"""

import os
import subprocess
import sys
import json

def check_auth_files():
    """Проверить наличие файлов авторизации"""
    required_files = [
        'selenium_cookies.json',
        'storage.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы авторизации: {', '.join(missing_files)}")
        print("Запустите: python simple_auth.py")
        return False
    
    print("✅ Файлы авторизации найдены")
    return True

def get_server_info():
    """Получить информацию о сервере"""
    server_ip = input("Введите IP адрес сервера: ").strip()
    server_user = input("Введите пользователя сервера (root): ").strip() or "root"
    return server_ip, server_user

def setup_server(server_ip, server_user):
    """Настроить сервер"""
    print("🔧 Настройка сервера...")
    
    commands = [
        "apt update && apt upgrade -y",
        "apt install -y python3 python3-pip git curl wget",
        "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -",
        'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list',
        "apt update",
        "apt install -y google-chrome-stable ffmpeg",
        "useradd -m -s /bin/bash meetingbot || true",
        "usermod -aG audio meetingbot || true",
        "cd /opt && git clone https://github.com/goqorhopar/b24.git meeting-bot || (cd meeting-bot && git pull)",
        "chown -R meetingbot:meetingbot /opt/meeting-bot",
        "cd /opt/meeting-bot && pip3 install -r requirements.txt"
    ]
    
    for cmd in commands:
        print(f"Выполняется: {cmd}")
        result = subprocess.run([
            "ssh", f"{server_user}@{server_ip}", cmd
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ Предупреждение: {result.stderr}")
        else:
            print("✅ Выполнено")

def copy_auth_files(server_ip, server_user):
    """Скопировать файлы авторизации"""
    print("🔐 Копирование файлов авторизации...")
    
    files_to_copy = [
        "selenium_cookies.json",
        "storage.json"
    ]
    
    # Добавляем все файлы cookies и storage
    for file in os.listdir("."):
        if file.startswith("cookies_") and file.endswith(".json"):
            files_to_copy.append(file)
        elif file.startswith("storage_") and file.endswith(".json"):
            files_to_copy.append(file)
    
    for file in files_to_copy:
        if os.path.exists(file):
            print(f"Копируется: {file}")
            result = subprocess.run([
                "scp", file, f"{server_user}@{server_ip}:/opt/meeting-bot/"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {file} скопирован")
            else:
                print(f"❌ Ошибка копирования {file}: {result.stderr}")

def test_auth_on_server(server_ip, server_user):
    """Протестировать авторизацию на сервере"""
    print("🧪 Тестирование авторизации на сервере...")
    
    result = subprocess.run([
        "ssh", f"{server_user}@{server_ip}", 
        "cd /opt/meeting-bot && python3 check_auth.py"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Ошибки:", result.stderr)
    
    return result.returncode == 0

def start_bot_on_server(server_ip, server_user):
    """Запустить бота на сервере"""
    print("🤖 Запуск бота на сервере...")
    
    # Создаем systemd сервис
    service_content = """[Unit]
Description=Meeting Bot
After=network.target

[Service]
Type=simple
User=meetingbot
WorkingDirectory=/opt/meeting-bot
ExecStart=/usr/bin/python3 meeting-bot.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/meeting-bot

[Install]
WantedBy=multi-user.target"""
    
    # Записываем сервис
    subprocess.run([
        "ssh", f"{server_user}@{server_ip}", 
        f"cat > /etc/systemd/system/meeting-bot.service << 'EOF'\n{service_content}\nEOF"
    ])
    
    # Активируем сервис
    subprocess.run([
        "ssh", f"{server_user}@{server_ip}", 
        "systemctl daemon-reload && systemctl enable meeting-bot && systemctl start meeting-bot"
    ])
    
    print("✅ Бот запущен как systemd сервис")

def main():
    """Главная функция"""
    print("🚀 Автоматический деплой Meeting Bot")
    print("=" * 40)
    
    # Проверяем файлы авторизации
    if not check_auth_files():
        return 1
    
    # Получаем информацию о сервере
    server_ip, server_user = get_server_info()
    
    try:
        # Настраиваем сервер
        setup_server(server_ip, server_user)
        
        # Копируем файлы авторизации
        copy_auth_files(server_ip, server_user)
        
        # Тестируем авторизацию
        if test_auth_on_server(server_ip, server_user):
            print("✅ Авторизация работает на сервере")
            
            # Запускаем бота
            start_bot_on_server(server_ip, server_user)
            
            print("\n🎉 Деплой завершен успешно!")
            print("📋 Команды для управления:")
            print(f"  Статус: ssh {server_user}@{server_ip} 'systemctl status meeting-bot'")
            print(f"  Логи: ssh {server_user}@{server_ip} 'journalctl -u meeting-bot -f'")
            print(f"  Остановка: ssh {server_user}@{server_ip} 'systemctl stop meeting-bot'")
        else:
            print("❌ Ошибка авторизации на сервере")
            return 1
            
    except Exception as e:
        print(f"❌ Ошибка деплоя: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
