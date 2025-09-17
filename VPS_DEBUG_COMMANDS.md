# Команды для отладки бота на VPS

## 1. Подключение к VPS
```bash
ssh root@pwifzybfye
```

## 2. Проверка статуса бота
```bash
systemctl status telegram-bot --no-pager
```

## 3. Просмотр логов
```bash
journalctl -u telegram-bot -n 50 --no-pager
```

## 4. Остановка бота
```bash
systemctl stop telegram-bot
```

## 5. Переход в директорию
```bash
cd /opt/telegram-bot
```

## 6. Проверка текущих файлов
```bash
ls -la real_meeting_automation.py
head -20 real_meeting_automation.py
```

## 7. Применение исправлений
```bash
# Скачиваем исправленный файл
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Проверяем, что файл скачался
ls -la real_meeting_automation.py
```

## 8. Очистка кеша
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

## 9. Перезапуск бота
```bash
systemctl start telegram-bot
```

## 10. Проверка статуса после перезапуска
```bash
systemctl status telegram-bot --no-pager
```

## 11. Мониторинг логов в реальном времени
```bash
journalctl -u telegram-bot -f
```

## 12. Тестирование бота
Отправьте боту ссылку на встречу и следите за логами.

## Альтернативный способ - полный скрипт
```bash
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/deploy_all_platforms_fix.sh | bash
```

## Если бот не отвечает на сообщения
```bash
# Проверяем, что бот запущен
ps aux | grep python

# Проверяем порт
netstat -tlnp | grep 3000

# Проверяем переменные окружения
cat .env
```
