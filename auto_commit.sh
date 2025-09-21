#!/bin/bash
# Автоматический коммит изменений

echo "Автоматический коммит..."

# Проверяем есть ли изменения
if git diff --quiet && git diff --cached --quiet; then
    echo "Нет изменений для коммита"
    exit 0
fi

# Добавляем все изменения
git add .

# Создаем коммит с текущим временем
commit_message="Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_message"

if [ $? -eq 0 ]; then
    echo "Автоматический коммит выполнен: $commit_message"
    
    # Запускаем автоматический деплой
    python auto_deploy.py --commit
    
    if [ $? -eq 0 ]; then
        echo "Автоматический деплой выполнен"
    else
        echo "Ошибка автоматического деплоя"
    fi
else
    echo "Ошибка автоматического коммита"
    exit 1
fi
