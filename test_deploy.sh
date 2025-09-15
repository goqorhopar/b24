#!/bin/bash

# Скрипт для тестирования деплоя
# Запускать локально для проверки перед пушем в GitHub

set -e

echo "🧪 Тестируем деплой локально..."

# Проверяем синтаксис Python файлов
echo "🔍 Проверяем синтаксис Python файлов..."
python -m py_compile main.py
python -m py_compile config.py
python -m py_compile db.py
python -m py_compile bitrix.py
python -m py_compile gemini_client.py
python -m py_compile utils.py
echo "✅ Синтаксис корректен!"

# Проверяем конфигурацию
echo "⚙️ Проверяем конфигурацию..."
python -c "
import sys
sys.path.append('.')
try:
    from config import *
    print('✅ Конфигурация загружена успешно')
except Exception as e:
    print(f'❌ Ошибка в конфигурации: {e}')
    sys.exit(1)
"

# Проверяем зависимости
echo "📦 Проверяем зависимости..."
pip install -r requirements.txt
echo "✅ Зависимости установлены!"

# Проверяем файлы деплоя
echo "📋 Проверяем файлы деплоя..."
if [ -f ".github/workflows/deploy.yml" ]; then
    echo "✅ GitHub Actions workflow найден"
else
    echo "❌ GitHub Actions workflow не найден"
    exit 1
fi

if [ -f "deploy_vps_github.sh" ]; then
    echo "✅ Скрипт деплоя найден"
else
    echo "❌ Скрипт деплоя не найден"
    exit 1
fi

if [ -f "setup_vps.sh" ]; then
    echo "✅ Скрипт настройки VPS найден"
else
    echo "❌ Скрипт настройки VPS не найден"
    exit 1
fi

# Проверяем .env.example
if [ -f ".env.example" ]; then
    echo "✅ Файл .env.example найден"
else
    echo "⚠️ Файл .env.example не найден"
fi

echo ""
echo "🎉 Все проверки пройдены успешно!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Убедитесь, что все изменения закоммичены:"
echo "   git add ."
echo "   git commit -m 'Настройка автоматического деплоя'"
echo ""
echo "2. Запушьте изменения в GitHub:"
echo "   git push origin main"
echo ""
echo "3. GitHub Actions автоматически запустит деплой"
echo ""
echo "4. Проверьте статус деплоя в GitHub Actions"
