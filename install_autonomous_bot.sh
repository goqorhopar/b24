#!/bin/bash

echo "🚀 Установка автономного бота на сервер..."

# Копируем сервис
sudo cp meeting-bot.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable meeting-bot.service

# Запускаем бота
sudo systemctl start meeting-bot.service

# Проверяем статус
sudo systemctl status meeting-bot.service

echo "✅ Бот установлен и запущен!"
echo "📋 Команды управления:"
echo "  sudo systemctl status meeting-bot.service  - статус"
echo "  sudo systemctl restart meeting-bot.service  - перезапуск"
echo "  sudo systemctl stop meeting-bot.service     - остановка"
echo "  sudo journalctl -u meeting-bot.service -f   - логи"
echo ""
echo "🤖 Бот будет автоматически запускаться при перезагрузке сервера!"
