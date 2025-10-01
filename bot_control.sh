#!/bin/bash

SERVICE_NAME="meeting-bot"

case "$1" in
    start)
        echo "Запуск Meeting Bot..."
        systemctl start $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    stop)
        echo "Остановка Meeting Bot..."
        systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Перезапуск Meeting Bot..."
        systemctl restart $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    status)
        systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "Просмотр логов Meeting Bot (Ctrl+C для выхода)..."
        journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo "Включение автозапуска Meeting Bot..."
        systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "Отключение автозапуска Meeting Bot..."
        systemctl disable $SERVICE_NAME
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|enable|disable}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  status  - Показать статус"
        echo "  logs    - Показать логи в реальном времени"
        echo "  enable  - Включить автозапуск"
        echo "  disable - Отключить автозапуск"
        exit 1
        ;;
esac
