#!/bin/bash

echo "=== Установка Meeting Bot на сервер ==="

# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip python3-venv ffmpeg chromium-browser

# Устанавливаем зависимости Python
pip3 install -r requirements.txt

# Создаем директорию для записей
mkdir -p /tmp/recordings
chmod 755 /tmp/recordings

# Копируем systemd сервис
cp meeting-bot.service /etc/systemd/system/

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable meeting-bot

echo "=== Установка завершена ==="
echo ""
echo "Для запуска бота:"
echo "  systemctl start meeting-bot"
echo ""
echo "Для проверки статуса:"
echo "  systemctl status meeting-bot"
echo ""
echo "Для просмотра логов:"
echo "  journalctl -u meeting-bot -f"
echo ""
echo "Для остановки:"
echo "  systemctl stop meeting-bot"
echo ""
echo "ВАЖНО: Создайте файл .env с настройками перед запуском!"
