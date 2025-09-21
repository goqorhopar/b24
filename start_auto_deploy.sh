#!/bin/bash
# Запуск автоматического деплоя

echo "Запускаю автоматический деплой..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "Файл .env не найден!"
    echo "Скопируйте env_example.txt в .env и заполните настройки:"
    echo "   cp env_example.txt .env"
    echo "   nano .env"
    exit 1
fi

# Запускаем отслеживание файлов в фоне
echo "Запускаю отслеживание изменений файлов..."
python file_watcher.py &

# Сохраняем PID процесса
echo $! > file_watcher.pid

echo "Автоматический деплой запущен"
echo "PID процесса отслеживания: $(cat file_watcher.pid)"
echo "Для остановки: kill $(cat file_watcher.pid)"
