#!/bin/bash

# ===========================================
# НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ
# ===========================================

set -e

echo "⚙️ Настраиваю автоматический деплой Meeting Bot..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3."
    exit 1
fi

# Проверяем наличие git
if ! command -v git &> /dev/null; then
    echo "❌ Git не найден. Установите Git."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📋 Скопируйте env_example.txt в .env и заполните настройки:"
    echo "   cp env_example.txt .env"
    echo "   nano .env"
    exit 1
fi

echo "🔍 Проверяю настройки автоматического деплоя..."

# Проверяем настройки GitHub
if ! grep -q "GITHUB_REPO=" .env || grep -q "GITHUB_REPO=your_username/meeting-bot" .env; then
    echo "❌ GITHUB_REPO не настроен в .env"
    echo "   Укажите ваш репозиторий в формате: username/repo-name"
    exit 1
fi

if ! grep -q "GITHUB_TOKEN=" .env || grep -q "GITHUB_TOKEN=your_github_token_here" .env; then
    echo "❌ GITHUB_TOKEN не настроен в .env"
    echo "   Получите токен в GitHub: Settings > Developer settings > Personal access tokens"
    exit 1
fi

# Проверяем настройки сервера
if ! grep -q "DEPLOY_SERVER_URL=" .env || grep -q "DEPLOY_SERVER_URL=your_server_ip_or_domain" .env; then
    echo "❌ DEPLOY_SERVER_URL не настроен в .env"
    echo "   Укажите IP адрес или домен вашего сервера"
    exit 1
fi

echo "✅ Настройки проверены"

# Настраиваем git
echo "🔧 Настраиваю Git..."
git config user.name "Auto Deployer" || true
git config user.email "auto-deployer@meeting-bot.local" || true

# Создаем директорию .github/workflows если не существует
mkdir -p .github/workflows

# Запускаем настройку автоматического деплоя
echo "🚀 Запускаю настройку автоматического деплоя..."
python3 auto_deploy.py --setup

if [ $? -eq 0 ]; then
    echo "✅ Автоматический деплой настроен"
else
    echo "❌ Ошибка настройки автоматического деплоя"
    exit 1
fi

echo ""
echo "🎉 Настройка автоматического деплоя завершена!"
echo ""
echo "📋 Что было настроено:"
echo "   ✅ GitHub Actions workflow"
echo "   ✅ Скрипт быстрого деплоя"
echo "   ✅ Автоматические коммиты"
echo ""
echo "🔧 Следующие шаги:"
echo "   1. Добавьте SSH ключ в GitHub Secrets:"
echo "      - DEPLOY_SERVER_URL"
echo "      - DEPLOY_SERVER_USER"
echo "      - DEPLOY_SSH_KEY"
echo "      - DEPLOY_SSH_PORT (опционально)"
echo "      - DEPLOY_SERVER_PATH (опционально)"
echo ""
echo "   2. Для быстрого деплоя используйте:"
echo "      ./quick_deploy.sh"
echo ""
echo "   3. Для автоматического деплоя при каждом push:"
echo "      git add ."
echo "      git commit -m 'Update'"
echo "      git push origin main"
echo ""
echo "📖 Подробная документация: SERVER_DEPLOYMENT_GUIDE.md"
