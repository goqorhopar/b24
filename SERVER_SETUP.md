# Настройка Meeting Bot для работы 24/7 на сервере

## Что уже готово:

✅ **Исправлен код бота** - убрана имитация подключения, добавлена проверка реального состояния встречи
✅ **Настроен headless режим** - бот работает без GUI на сервере
✅ **Создан systemd сервис** - автозапуск при перезагрузке сервера
✅ **Добавлен мониторинг** - автоматический перезапуск при сбоях
✅ **Настроены уведомления** - получаешь сообщения в Telegram о статусе

## Команды для запуска на сервере:

### 1. Установка (выполнить один раз):
```bash
# Сделать скрипты исполняемыми
chmod +x install_server.sh bot_control.sh server_commands.sh

# Запустить установку
./install_server.sh
```

### 2. Настройка переменных окружения:
```bash
# Скопировать настройки
cp env_production.txt .env

# Отредактировать .env файл - добавить TELEGRAM_BOT_TOKEN
nano .env
```

### 3. Запуск бота:
```bash
# Запустить бота
systemctl start meeting-bot

# Включить автозапуск
systemctl enable meeting-bot

# Запустить мониторинг
systemctl start meeting-bot-monitor
systemctl enable meeting-bot-monitor
```

### 4. Проверка работы:
```bash
# Проверить статус
./server_commands.sh

# Или вручную:
systemctl status meeting-bot
systemctl status meeting-bot-monitor
```

## Управление ботом:

```bash
# Использовать скрипт управления
./bot_control.sh start    # Запустить
./bot_control.sh stop     # Остановить
./bot_control.sh restart  # Перезапустить
./bot_control.sh status   # Статус
./bot_control.sh logs     # Логи в реальном времени
```

## Что происходит автоматически:

🔄 **Автозапуск** - бот запускается при перезагрузке сервера
🔄 **Автоперезапуск** - если бот упал, мониторинг его перезапустит
📱 **Уведомления** - получаешь сообщения в Telegram о:
   - Запуске бота на сервере
   - Перезапуске при сбоях
   - Ежедневном статусе работы
   - Критических ошибках

## Мониторинг:

- **Проверка каждые 5 минут** - мониторинг проверяет работу бота
- **Максимум 3 попытки перезапуска** - если не помогает, отправляет уведомление
- **Ежедневные отчеты** - каждый день получаешь статус работы
- **Логи** - все события записываются в systemd journal

## Файлы на сервере:

- `/root/b24/meeting-bot.py` - основной бот
- `/root/b24/monitor_bot.py` - мониторинг
- `/root/b24/.env` - настройки
- `/etc/systemd/system/meeting-bot.service` - сервис бота
- `/etc/systemd/system/meeting-bot-monitor.service` - сервис мониторинга

## Логи:

```bash
# Логи бота
journalctl -u meeting-bot -f

# Логи мониторинга
journalctl -u meeting-bot-monitor -f

# Все логи
journalctl -u meeting-bot* -f
```

## Важно:

1. **Добавь TELEGRAM_BOT_TOKEN** в файл `.env`
2. **Бот работает в headless режиме** - без GUI
3. **Мониторинг автоматически перезапускает** бота при сбоях
4. **Получаешь уведомления** в Telegram о всех событиях
5. **Бот работает 24/7** без твоего участия

## Если что-то пошло не так:

```bash
# Проверить статус
systemctl status meeting-bot meeting-bot-monitor

# Посмотреть логи
journalctl -u meeting-bot -n 50

# Перезапустить все
systemctl restart meeting-bot meeting-bot-monitor
```

**Готово! Бот будет работать 24/7 на сервере и автоматически обрабатывать встречи.**