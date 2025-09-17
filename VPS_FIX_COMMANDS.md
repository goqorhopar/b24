# Команды для исправления бота на VPS

## 1. Подключение к VPS
```bash
ssh root@pwifzybfye
```

## 2. Остановка бота
```bash
systemctl stop telegram-bot
```

## 3. Переход в директорию проекта
```bash
cd /opt/telegram-bot
```

## 4. Создание резервных копий
```bash
cp real_meeting_automation.py real_meeting_automation.py.backup
cp meeting_link_processor.py meeting_link_processor.py.backup
```

## 5. Скачивание исправленных файлов
```bash
# Скачиваем исправленный real_meeting_automation.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Скачиваем исправленный meeting_link_processor.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py
```

## 6. Очистка кеша Python
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

## 7. Перезапуск бота
```bash
systemctl start telegram-bot
```

## 8. Проверка статуса
```bash
systemctl status telegram-bot --no-pager
```

## 9. Просмотр логов
```bash
journalctl -u telegram-bot -f
```

## Альтернативный способ - выполнение скрипта
```bash
# Скачиваем и выполняем скрипт деплоя
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/deploy_meeting_fixes.sh -o deploy_meeting_fixes.sh
chmod +x deploy_meeting_fixes.sh
./deploy_meeting_fixes.sh
```

## Что исправлено:

1. **Импорты в meeting_link_processor.py** - исправлен импорт с `meeting_automation` на `real_meeting_automation`
2. **Chrome WebDriver настройки** - обновлен headless режим на `--headless=new`
3. **Логика присоединения к Zoom** - улучшена надежность присоединения
4. **Методы интерфейса** - добавлены недостающие методы `is_in_meeting()` и `join_meeting()`
5. **Обработка ошибок** - улучшена обработка ошибок и таймауты

## Тестирование:
После деплоя отправьте боту ссылку на Zoom встречу для проверки работы.
