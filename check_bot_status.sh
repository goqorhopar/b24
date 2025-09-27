#!/bin/bash

echo "📊 Проверка статуса автономного бота..."

# Проверяем статус сервиса
echo "🔍 Статус сервиса:"
sudo systemctl status meeting-bot.service --no-pager

echo ""
echo "📝 Последние логи:"
sudo journalctl -u meeting-bot.service --no-pager -n 20

echo ""
echo "🔄 Проверка процессов:"
ps aux | grep autonomous_bot.py | grep -v grep

echo ""
echo "🌐 Проверка сетевых соединений:"
netstat -tulpn | grep python

echo ""
echo "📁 Проверка файлов:"
ls -la /root/b24/autonomous_bot.py
ls -la /etc/systemd/system/meeting-bot.service
