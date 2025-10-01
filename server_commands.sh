#!/bin/bash

echo "=== Meeting Bot Server Commands ==="
echo ""

# Проверяем статус бота
echo "1. Статус бота:"
systemctl status meeting-bot --no-pager -l

echo ""
echo "2. Статус мониторинга:"
systemctl status meeting-bot-monitor --no-pager -l

echo ""
echo "3. Последние логи бота (20 строк):"
journalctl -u meeting-bot -n 20 --no-pager

echo ""
echo "4. Последние логи мониторинга (10 строк):"
journalctl -u meeting-bot-monitor -n 10 --no-pager

echo ""
echo "=== Команды управления ==="
echo "Запуск бота:     systemctl start meeting-bot"
echo "Остановка бота:  systemctl stop meeting-bot"
echo "Перезапуск:      systemctl restart meeting-bot"
echo "Логи в реальном времени: journalctl -u meeting-bot -f"
echo ""
echo "Мониторинг:"
echo "Запуск мониторинга:     systemctl start meeting-bot-monitor"
echo "Остановка мониторинга:  systemctl stop meeting-bot-monitor"
echo "Логи мониторинга:       journalctl -u meeting-bot-monitor -f"
