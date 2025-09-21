"""
Скрипт для развертывания бота на сервере
"""
import os
import sys
import subprocess
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_command(command: str, description: str) -> bool:
    """Выполнить команду и проверить результат"""
    log.info(f"Выполняю: {description}")
    log.info(f"Команда: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        log.info(f"✅ {description} - успешно")
        if result.stdout:
            log.info(f"Вывод: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"❌ {description} - ошибка")
        log.error(f"Код ошибки: {e.returncode}")
        if e.stdout:
            log.error(f"Вывод: {e.stdout}")
        if e.stderr:
            log.error(f"Ошибка: {e.stderr}")
        return False

def check_system_requirements():
    """Проверка системных требований"""
    log.info("Проверка системных требований...")
    
    # Проверка Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        log.error("Требуется Python 3.8 или выше")
        return False
    log.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Проверка pip
    if not run_command("pip --version", "Проверка pip"):
        return False
    
    # Проверка git
    if not run_command("git --version", "Проверка git"):
        return False
    
    return True

def install_system_dependencies():
    """Установка системных зависимостей"""
    log.info("Установка системных зависимостей...")
    
    # Определение дистрибутива Linux
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read().lower()
    except:
        os_info = ""
    
    if 'ubuntu' in os_info or 'debian' in os_info:
        # Ubuntu/Debian
        commands = [
            "apt-get update",
            "apt-get install -y python3-pip python3-venv git curl wget",
            "apt-get install -y chromium-browser chromium-chromedriver",
            "apt-get install -y ffmpeg portaudio19-dev",
            "apt-get install -y pulseaudio pulseaudio-utils",
            "apt-get install -y alsa-utils",
            "apt-get install -y xvfb"  # Для headless режима
        ]
    elif 'centos' in os_info or 'rhel' in os_info or 'fedora' in os_info:
        # CentOS/RHEL/Fedora
        commands = [
            "yum update -y",
            "yum install -y python3-pip python3-venv git curl wget",
            "yum install -y chromium chromedriver",
            "yum install -y ffmpeg portaudio-devel",
            "yum install -y pulseaudio pulseaudio-utils",
            "yum install -y alsa-utils",
            "yum install -y xorg-x11-server-Xvfb"
        ]
    else:
        log.warning("Неизвестный дистрибутив Linux, пропускаю установку системных пакетов")
        return True
    
    for command in commands:
        if not run_command(f"sudo {command}", f"Установка: {command}"):
            log.warning(f"Не удалось выполнить: {command}")
    
    return True

def setup_python_environment():
    """Настройка Python окружения"""
    log.info("Настройка Python окружения...")
    
    # Создание виртуального окружения
    if not run_command("python3 -m venv venv", "Создание виртуального окружения"):
        return False
    
    # Активация виртуального окружения
    activate_script = "venv/bin/activate" if os.name != 'nt' else "venv\\Scripts\\activate"
    
    # Установка pip
    if not run_command(f"source {activate_script} && pip install --upgrade pip", "Обновление pip"):
        return False
    
    return True

def install_python_dependencies():
    """Установка Python зависимостей"""
    log.info("Установка Python зависимостей...")
    
    # Список зависимостей
    dependencies = [
        "selenium>=4.15.0",
        "flask>=2.3.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.0",
        "openai-whisper>=20231117",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "numpy>=1.24.0",
        "sounddevice>=0.4.6",
        "soundfile>=0.12.1",
        "pyaudio>=0.2.11",
        "opencv-python>=4.8.0",
        "pyautogui>=0.9.54",
        "psutil>=5.9.0"
    ]
    
    activate_script = "venv/bin/activate" if os.name != 'nt' else "venv\\Scripts\\activate"
    
    for dep in dependencies:
        if not run_command(f"source {activate_script} && pip install {dep}", f"Установка {dep}"):
            log.warning(f"Не удалось установить {dep}")
    
    return True

def setup_audio_system():
    """Настройка аудиосистемы"""
    log.info("Настройка аудиосистемы...")
    
    # Создание виртуального аудиоустройства для записи
    commands = [
        "pactl load-module module-null-sink sink_name=meeting_bot",
        "pactl load-module module-loopback source=meeting_bot.monitor sink=@DEFAULT_SINK@",
        "pactl set-default-source meeting_bot.monitor"
    ]
    
    for command in commands:
        if not run_command(command, f"Настройка аудио: {command}"):
            log.warning(f"Не удалось выполнить: {command}")
    
    return True

def create_systemd_service():
    """Создание systemd сервиса"""
    log.info("Создание systemd сервиса...")
    
    current_dir = os.getcwd()
    service_content = f"""[Unit]
Description=Meeting Bot Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={current_dir}
Environment=PATH={current_dir}/venv/bin
ExecStart={current_dir}/venv/bin/python main_server_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open('/etc/systemd/system/meeting-bot.service', 'w') as f:
            f.write(service_content)
        
        run_command("systemctl daemon-reload", "Перезагрузка systemd")
        run_command("systemctl enable meeting-bot", "Включение автозапуска")
        
        log.info("✅ Systemd сервис создан")
        return True
        
    except Exception as e:
        log.error(f"Ошибка при создании systemd сервиса: {e}")
        return False

def create_env_file():
    """Создание файла .env"""
    log.info("Создание файла .env...")
    
    env_content = """# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MODEL_FALLBACK=gemini-1.5-flash

# Bitrix24
BITRIX_WEBHOOK_URL=your_bitrix_webhook_url_here
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1

# Server Settings
NODE_ENV=production
LOG_LEVEL=INFO
PORT=3000

# Meeting Settings
MEETING_DISPLAY_NAME=Асистент Григория
MEETING_HEADLESS=true
MEETING_DURATION_MINUTES=60

# Admin
ADMIN_CHAT_ID=your_admin_chat_id_here

# Audio Settings
AUDIO_RECORDING_METHOD=auto
WHISPER_MODEL=base
WHISPER_LANGUAGE=ru

# Performance
MAX_CONCURRENT_MEETINGS=3
MEETING_TIMEOUT_SECONDS=3600
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        log.info("✅ Файл .env создан")
        log.info("⚠️  Не забудьте заполнить переменные окружения!")
        return True
        
    except Exception as e:
        log.error(f"Ошибка при создании .env файла: {e}")
        return False

def setup_firewall():
    """Настройка файрвола"""
    log.info("Настройка файрвола...")
    
    commands = [
        "ufw allow 3000/tcp",  # Основной порт бота
        "ufw allow 9090/tcp",  # Метрики
        "ufw allow ssh"        # SSH
    ]
    
    for command in commands:
        if not run_command(f"sudo {command}", f"Настройка файрвола: {command}"):
            log.warning(f"Не удалось выполнить: {command}")
    
    return True

def test_installation():
    """Тестирование установки"""
    log.info("Тестирование установки...")
    
    activate_script = "venv/bin/activate" if os.name != 'nt' else "venv\\Scripts\\activate"
    
    # Тест импорта основных модулей
    test_commands = [
        f"source {activate_script} && python -c 'import selenium; print(\"Selenium OK\")'",
        f"source {activate_script} && python -c 'import flask; print(\"Flask OK\")'",
        f"source {activate_script} && python -c 'import whisper; print(\"Whisper OK\")'",
        f"source {activate_script} && python -c 'import sounddevice; print(\"SoundDevice OK\")'"
    ]
    
    for command in test_commands:
        if not run_command(command, "Тест импорта модулей"):
            log.warning("Некоторые модули не импортируются корректно")
    
    return True

def main():
    """Основная функция развертывания"""
    log.info("🚀 Начинаю развертывание Meeting Bot на сервере")
    
    steps = [
        ("Проверка системных требований", check_system_requirements),
        ("Установка системных зависимостей", install_system_dependencies),
        ("Настройка Python окружения", setup_python_environment),
        ("Установка Python зависимостей", install_python_dependencies),
        ("Настройка аудиосистемы", setup_audio_system),
        ("Создание .env файла", create_env_file),
        ("Создание systemd сервиса", create_systemd_service),
        ("Настройка файрвола", setup_firewall),
        ("Тестирование установки", test_installation)
    ]
    
    for step_name, step_func in steps:
        log.info(f"\n{'='*50}")
        log.info(f"Шаг: {step_name}")
        log.info(f"{'='*50}")
        
        if not step_func():
            log.error(f"❌ Ошибка на шаге: {step_name}")
            log.error("Развертывание прервано")
            return False
    
    log.info(f"\n{'='*50}")
    log.info("✅ Развертывание завершено успешно!")
    log.info(f"{'='*50}")
    
    log.info("\n📋 Следующие шаги:")
    log.info("1. Отредактируйте файл .env и заполните все переменные")
    log.info("2. Запустите бота: sudo systemctl start meeting-bot")
    log.info("3. Проверьте статус: sudo systemctl status meeting-bot")
    log.info("4. Просмотрите логи: sudo journalctl -u meeting-bot -f")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
