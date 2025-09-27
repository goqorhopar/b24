#!/bin/bash

echo "🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ БОТА НА СЕРВЕР"
echo "БЕЗ УЧАСТИЯ ПОЛЬЗОВАТЕЛЯ!"

# Останавливаем старые процессы
pkill -f autonomous_bot.py 2>/dev/null || true
sudo systemctl stop meeting-bot.service 2>/dev/null || true

# Создаем директории
mkdir -p /root/b24/logs
chmod 755 /root/b24/logs

# Копируем файлы
cp autonomous_bot.py /root/b24/
cp meeting-bot.service /etc/systemd/system/

# Устанавливаем права
chmod +x /root/b24/autonomous_bot.py
chmod 644 /etc/systemd/system/meeting-bot.service

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable meeting-bot.service

# Запускаем бота
systemctl start meeting-bot.service

# Ждем запуска
sleep 5

# Проверяем статус
if systemctl is-active --quiet meeting-bot.service; then
    echo "✅ БОТ УСПЕШНО ЗАПУЩЕН АВТОМАТИЧЕСКИ!"
    echo "🤖 Работает без участия пользователя!"
    echo "📊 Статус: $(systemctl is-active meeting-bot.service)"
else
    echo "❌ Ошибка запуска бота"
    systemctl status meeting-bot.service --no-pager
    exit 1
fi

echo ""
echo "🎯 БОТ РАБОТАЕТ АВТОНОМНО!"
echo "📝 Логи: journalctl -u meeting-bot.service -f"
echo "🔄 Автоперезапуск при сбоях: ВКЛЮЧЕН"
echo "🚀 Автозапуск при перезагрузке: ВКЛЮЧЕН"
