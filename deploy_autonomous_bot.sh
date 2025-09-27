#!/bin/bash

echo "🚀 Деплой автономного бота на сервер..."

# Останавливаем старый бот если запущен
sudo systemctl stop meeting-bot.service 2>/dev/null || true

# Копируем файлы
sudo cp autonomous_bot.py /root/b24/
sudo cp meeting-bot.service /etc/systemd/system/

# Устанавливаем права
sudo chmod +x /root/b24/autonomous_bot.py
sudo chmod 644 /etc/systemd/system/meeting-bot.service

# Создаем директорию логов если не существует
sudo mkdir -p /root/b24/logs
sudo chmod 755 /root/b24/logs

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable meeting-bot.service

# Запускаем бота
sudo systemctl start meeting-bot.service

# Ждем 3 секунды
sleep 3

# Проверяем статус
echo "📊 Статус бота:"
sudo systemctl status meeting-bot.service --no-pager

echo ""
echo "📋 Логи бота:"
sudo journalctl -u meeting-bot.service --no-pager -n 10

echo ""
echo "✅ Автономный бот развернут и работает!"
echo "🤖 Бот будет автоматически запускаться при перезагрузке сервера!"
echo "📝 Логи: sudo journalctl -u meeting-bot.service -f"
