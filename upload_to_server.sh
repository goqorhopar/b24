#!/bin/bash
# Скрипт для загрузки файлов бота на сервер

echo "📤 Загрузка файлов бота на сервер"
echo "================================="

# Настройки сервера (ИЗМЕНИТЕ НА СВОИ!)
SERVER_IP="your-server-ip"
SERVER_USER="root"
SERVER_PATH="/tmp/meeting-bot"

echo "🔧 Настройки сервера:"
echo "  IP: $SERVER_IP"
echo "  Пользователь: $SERVER_USER"
echo "  Путь: $SERVER_PATH"
echo ""

# Проверка подключения
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Подключение успешно'"; then
    echo "❌ Не удается подключиться к серверу!"
    echo "Проверьте:"
    echo "  1. IP адрес сервера"
    echo "  2. Пользователя"
    echo "  3. SSH ключи или пароль"
    exit 1
fi

echo "✅ Подключение к серверу успешно"
echo ""

# Создание директории на сервере
echo "📁 Создание директории на сервере..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p $SERVER_PATH"

# Загрузка файлов
echo "📤 Загрузка файлов бота..."

# Основные файлы
scp main.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp config.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Модули бота
scp meeting_link_processor.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp aggressive_meeting_automation.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp speech_transcriber.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp meeting_analyzer.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp gemini_client.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp bitrix.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp bitrix_meeting_integration.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp platform_detector.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp db.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Скрипты развертывания
scp deploy_to_server.sh $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp SERVER_DEPLOYMENT_INSTRUCTIONS.md $SERVER_USER@$SERVER_IP:$SERVER_PATH/

echo "✅ Все файлы загружены на сервер"
echo ""

# Запуск развертывания
echo "🚀 Запуск развертывания на сервере..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_PATH && chmod +x deploy_to_server.sh && sudo ./deploy_to_server.sh"

echo ""
echo "🎉 Развертывание завершено!"
echo "=========================="
echo ""
echo "📋 Для управления ботом на сервере используйте:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  sudo /opt/meeting-bot/manage_bot.sh status"
echo "  sudo /opt/meeting-bot/manage_bot.sh logs"
echo ""
echo "✅ Бот готов к работе на сервере!"
