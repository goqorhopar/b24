#!/bin/bash

echo "🔧 НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ ДЛЯ СУЩЕСТВУЮЩЕГО РЕПОЗИТОРИЯ"
echo "================================================================="

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git и повторите попытку."
    exit 1
fi

echo "📋 Настройка существующего репозитория..."

# Проверка существования .git
if [ ! -d ".git" ]; then
    echo "❌ Git репозиторий не найден. Инициализируйте Git или клонируйте репозиторий."
    exit 1
fi

# Добавление всех файлов
echo "📁 Добавление файлов в Git..."
git add .

# Коммит изменений
echo "💾 Коммит изменений..."
git commit -m "Add auto-deploy system: $(date)"

echo ""
echo "🚀 НАСТРОЙКА GITHUB SECRETS"
echo "============================"
echo ""
echo "1. Перейдите в ваш репозиторий на GitHub"
echo "2. Settings → Secrets and variables → Actions"
echo "3. Добавьте следующие секреты:"
echo ""
echo "   SERVER_HOST: 109.172.47.253"
echo "   SERVER_USER: root"
echo "   SERVER_SSH_KEY: [приватный SSH ключ с сервера]"
echo ""
echo "4. На сервере создайте SSH ключ:"
echo "   ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N \"\""
echo "   cat /root/.ssh/id_rsa.pub  # Добавьте в GitHub SSH keys"
echo "   cat /root/.ssh/id_rsa      # Добавьте в SERVER_SSH_KEY secret"
echo ""
echo "5. Загрузите изменения:"
echo "   git push origin main"
echo ""
echo "✅ После настройки:"
echo "   - GitHub Actions автоматически задеплоит на сервер"
echo "   - Бот будет обновляться без вашего участия!"
