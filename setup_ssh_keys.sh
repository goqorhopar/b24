#!/bin/bash

# Скрипт для настройки SSH ключей для автодеплоя
# Запуск: ./setup_ssh_keys.sh

set -e

VPS_IP="109.172.47.253"
VPS_USER="root"
VPS_PASSWORD="MmSS0JSm%6vb"

echo "🔑 Настройка SSH ключей для автодеплоя"
echo "======================================"

# Проверяем наличие ssh-keygen
if ! command -v ssh-keygen &> /dev/null; then
    echo "❌ ssh-keygen не найден. Установите OpenSSH."
    exit 1
fi

# Создаем директорию для ключей если не существует
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Проверяем существование ключей
if [ -f ~/.ssh/id_rsa ] && [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ SSH ключи уже существуют"
    echo "📋 Публичный ключ:"
    cat ~/.ssh/id_rsa.pub
else
    echo "🔑 Создаем новые SSH ключи..."
    ssh-keygen -t rsa -b 4096 -C "deploy@telegram-bot" -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH ключи созданы"
fi

echo ""
echo "📋 Публичный ключ для добавления на VPS:"
echo "========================================"
cat ~/.ssh/id_rsa.pub
echo "========================================"

echo ""
echo "🔧 Добавляем публичный ключ на VPS..."

# Используем sshpass для автоматической установки ключа
if command -v sshpass &> /dev/null; then
    sshpass -p "$VPS_PASSWORD" ssh-copy-id -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP"
    echo "✅ Публичный ключ добавлен на VPS"
else
    echo "⚠️ sshpass не найден. Добавьте ключ вручную:"
    echo "ssh-copy-id $VPS_USER@$VPS_IP"
    echo "Или скопируйте публичный ключ выше в ~/.ssh/authorized_keys на VPS"
fi

echo ""
echo "🧪 Тестируем SSH подключение без пароля..."
if ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo 'SSH подключение работает!'" 2>/dev/null; then
    echo "✅ SSH подключение настроено успешно!"
else
    echo "❌ SSH подключение не работает. Проверьте настройки."
fi

echo ""
echo "📋 Следующие шаги:"
echo "1. Добавьте приватный ключ в GitHub Secrets:"
echo "   - VPS_HOST: $VPS_IP"
echo "   - VPS_USERNAME: $VPS_USER"
echo "   - VPS_SSH_KEY: содержимое ~/.ssh/id_rsa"
echo ""
echo "2. Настройте webhook в GitHub:"
echo "   - URL: http://$VPS_IP/deploy_webhook.php"
echo "   - Secret: your-secret-key-here"
echo ""
echo "3. Разместите deploy_webhook.php на VPS в корне веб-сервера"
echo ""
echo "4. Настройте права доступа:"
echo "   chmod 755 /var/www/html/deploy_webhook.php"
echo "   chown www-data:www-data /var/www/html/deploy_webhook.php"
