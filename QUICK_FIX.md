# 🚨 БЫСТРОЕ ИСПРАВЛЕНИЕ БОТА

## Выполните эти команды на VPS сервере:

```bash
# Подключение к VPS
ssh root@pwifzybfye

# Остановка бота
systemctl stop telegram-bot

# Переход в директорию
cd /opt/telegram-bot

# Скачивание исправленного файла
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Очистка кеша
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапуск бота
systemctl start telegram-bot

# Проверка статуса
systemctl status telegram-bot --no-pager
```

## Или одной командой:
```bash
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/emergency_fix.sh | bash
```

## После исправления:
1. Отправьте боту ссылку на встречу
2. Следите за логами: `journalctl -u telegram-bot -f`
3. Бот должен присоединиться к встрече

## Поддерживаемые платформы:
- ✅ Zoom (zoom.us, us05web.zoom.us)
- ✅ Google Meet (meet.google.com)
- ✅ Microsoft Teams (teams.microsoft.com)
- ✅ Контур.Толк (ktalk.ru, talk.kontur.ru)
- ✅ Яндекс Телемост (telemost.yandex.ru)
