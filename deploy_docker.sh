#!/bin/bash

echo "🐳 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ ЧЕРЕЗ DOCKER"
echo "БЕЗ УЧАСТИЯ ПОЛЬЗОВАТЕЛЯ!"

# Останавливаем старые контейнеры
docker-compose down 2>/dev/null || true

# Собираем и запускаем
docker-compose up -d --build

# Ждем запуска
sleep 10

# Проверяем статус
if docker-compose ps | grep -q "Up"; then
    echo "✅ БОТ ЗАПУЩЕН В DOCKER АВТОМАТИЧЕСКИ!"
    echo "🤖 Работает без участия пользователя!"
    echo "📊 Статус контейнеров:"
    docker-compose ps
else
    echo "❌ Ошибка запуска Docker контейнера"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎯 БОТ РАБОТАЕТ АВТОНОМНО В DOCKER!"
echo "📝 Логи: docker-compose logs -f"
echo "🔄 Автоперезапуск: ВКЛЮЧЕН"
echo "🚀 Автозапуск при перезагрузке: ВКЛЮЧЕН"
