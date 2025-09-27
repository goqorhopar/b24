#!/bin/bash

echo "🔧 НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ"
echo "===================================="

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git и повторите попытку."
    exit 1
fi

echo "📋 Настройка Git репозитория..."

# Инициализация Git если не существует
if [ ! -d ".git" ]; then
    echo "🔧 Инициализация Git репозитория..."
    git init
    git add .
    git commit -m "Initial commit: Autonomous Meeting Bot"
fi

# Добавление всех файлов
echo "📁 Добавление файлов в Git..."
git add .

# Коммит изменений
echo "💾 Коммит изменений..."
git commit -m "Auto-deploy setup: $(date)"

echo ""
echo "🚀 НАСТРОЙКА GITHUB РЕПОЗИТОРИЯ"
echo "==============================="
echo ""
echo "1. Создайте репозиторий на GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Добавьте remote origin:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo ""
echo "3. Загрузите код:"
echo "   git push -u origin main"
echo ""
echo "4. Настройте GitHub Secrets:"
echo "   - Перейдите в Settings → Secrets and variables → Actions"
echo "   - Добавьте следующие секреты:"
echo ""
echo "   SERVER_HOST: 109.172.47.253"
echo "   SERVER_USER: root"
echo "   SERVER_SSH_KEY: [ваш приватный SSH ключ]"
echo ""
echo "5. На сервере настройте Git:"
echo "   cd /root/b24"
echo "   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
echo "   chmod +x deploy_autonomous_server.sh"
echo "   ./deploy_autonomous_server.sh"
echo ""
echo "✅ После настройки:"
echo "   - Любые изменения в файлах автоматически попадут в GitHub"
echo "   - GitHub Actions автоматически задеплоит на сервер"
echo "   - Бот будет обновляться без вашего участия!"
