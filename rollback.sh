#!/bin/bash

# Скрипт для отката к предыдущей версии
# Использование: ./rollback.sh [количество коммитов назад]

set -e

VPS_IP="109.172.47.253"
VPS_USER="root"
PROJECT_DIR="/opt/telegram-bot"
COMMITS_BACK=${1:-1}

echo "🔄 Откат к предыдущей версии"
echo "============================="
echo "Сервер: $VPS_IP"
echo "Директория: $PROJECT_DIR"
echo "Коммитов назад: $COMMITS_BACK"
echo ""

# Функция для выполнения команд на VPS
run_ssh() {
    ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

echo "📋 Шаг 1: Подключение к серверу..."
if ! run_ssh "echo 'Подключение успешно'"; then
    echo "❌ Не удалось подключиться к серверу"
    exit 1
fi

echo "📋 Шаг 2: Остановка сервиса..."
run_ssh "systemctl stop telegram-bot"

echo "📋 Шаг 3: Переход в директорию проекта..."
run_ssh "cd $PROJECT_DIR"

echo "📋 Шаг 4: Сохранение текущего состояния..."
run_ssh "cd $PROJECT_DIR && git log --oneline -5"

echo "📋 Шаг 5: Откат к предыдущей версии..."
run_ssh "cd $PROJECT_DIR && git reset --hard HEAD~$COMMITS_BACK"

echo "📋 Шаг 6: Обновление зависимостей..."
run_ssh "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

echo "📋 Шаг 7: Перезапуск сервиса..."
run_ssh "systemctl start telegram-bot"

echo "📋 Шаг 8: Проверка статуса..."
run_ssh "systemctl status telegram-bot --no-pager"

echo "📋 Шаг 9: Тестирование приложения..."
sleep 5
if run_ssh "curl -f http://localhost:3000"; then
    echo "✅ Приложение работает"
else
    echo "❌ Приложение не отвечает"
    echo "📋 Проверьте логи: journalctl -u telegram-bot -f"
fi

echo ""
echo "✅ Откат завершен!"
echo "📊 Текущий коммит:"
run_ssh "cd $PROJECT_DIR && git log --oneline -1"

echo ""
echo "🔧 Полезные команды:"
echo "   Просмотр логов: journalctl -u telegram-bot -f"
echo "   Статус сервиса: systemctl status telegram-bot"
echo "   Перезапуск: systemctl restart telegram-bot"
