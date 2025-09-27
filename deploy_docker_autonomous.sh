#!/bin/bash

echo "🐳 ДЕПЛОЙ АВТОНОМНОГО БОТА В DOCKER"
echo "===================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

echo "🛑 Остановка старых контейнеров..."
docker-compose -f docker-compose.autonomous.yml down 2>/dev/null || true
docker stop autonomous-meeting-bot 2>/dev/null || true
docker rm autonomous-meeting-bot 2>/dev/null || true

echo "🏗️ Сборка Docker образа..."
docker-compose -f docker-compose.autonomous.yml build --no-cache

echo "🚀 Запуск автономного бота..."
docker-compose -f docker-compose.autonomous.yml up -d

echo "⏳ Ожидание запуска..."
sleep 10

echo "📊 Проверка статуса контейнера..."
docker ps | grep autonomous-meeting-bot

echo "📋 Проверка логов..."
docker logs autonomous-meeting-bot --tail 20

echo ""
echo "✅ АВТОНОМНЫЙ БОТ В DOCKER РАЗВЕРНУТ!"
echo "===================================="
echo "🐳 Бот работает в Docker контейнере"
echo "🔄 Автоматический перезапуск при сбоях"
echo "🚀 Автоматический запуск при перезагрузке сервера"
echo ""
echo "📋 Команды управления:"
echo "  docker ps                                    # Статус контейнеров"
echo "  docker logs autonomous-meeting-bot -f        # Логи в реальном времени"
echo "  docker restart autonomous-meeting-bot        # Перезапуск"
echo "  docker stop autonomous-meeting-bot           # Остановка"
echo "  docker-compose -f docker-compose.autonomous.yml down  # Полная остановка"
echo ""
echo "🎯 БОТ РАБОТАЕТ АВТОНОМНО В DOCKER!"
