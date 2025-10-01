# 🎉 Meeting Bot готов к работе на сервере!

## ✅ Что уже готово:

1. **Файлы загружены** в `/opt/meeting-bot/` на сервере
2. **Код исправлен** - убрана имитация подключения
3. **Systemd сервисы** настроены для автозапуска
4. **Мониторинг** добавлен для автоперезапуска
5. **Уведомления** настроены в Telegram

## 🚀 Команды для запуска на сервере:

### 1. Подключись к серверу:
```bash
ssh root@109.172.47.253
```

### 2. Перейди в директорию:
```bash
cd /opt/meeting-bot
```

### 3. Установи сервисы:
```bash
chmod +x *.sh
./install_server.sh
```

### 4. Настрой .env файл:
```bash
nano .env
```

**Добавь в .env:**
```
TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather
TELEGRAM_CHAT_ID=7537953397
ADMIN_CHAT_ID=7537953397
GITHUB_TOKEN=твой_github_token
GITHUB_REPO=goqorhopar/b24
WHISPER_MODEL=medium
RECORD_DIR=/tmp/recordings
MEETING_TIMEOUT_MIN=180
```

### 5. Запусти бота:
```bash
systemctl start meeting-bot
systemctl start meeting-bot-monitor
```

### 6. Включи автозапуск:
```bash
systemctl enable meeting-bot
systemctl enable meeting-bot-monitor
```

## 📊 Проверка работы:

### Статус сервисов:
```bash
systemctl status meeting-bot
systemctl status meeting-bot-monitor
```

### Логи в реальном времени:
```bash
journalctl -u meeting-bot -f
journalctl -u meeting-bot-monitor -f
```

### Быстрая проверка:
```bash
./server_commands.sh
```

## 🎯 Что получишь:

- **Уведомление о запуске** бота на сервере
- **Автоматические перезапуски** при сбоях
- **Ежедневные отчеты** о работе
- **Уведомления об ошибках** в Telegram
- **Работа 24/7** без твоего участия

## 🔧 Управление:

```bash
# Запуск
systemctl start meeting-bot meeting-bot-monitor

# Остановка
systemctl stop meeting-bot meeting-bot-monitor

# Перезапуск
systemctl restart meeting-bot meeting-bot-monitor

# Статус
systemctl status meeting-bot meeting-bot-monitor
```

## 📱 Уведомления в Telegram:

Бот отправит тебе сообщения:
- 🚀 О запуске на сервере
- ✅ О успешном подключении к встречам
- ❌ Об ошибках и имитации подключения
- 📊 Ежедневные отчеты о работе

## 🎉 Готово!

**Бот будет работать 24/7 на сервере и автоматически:**
- Присоединяться к встречам
- Проверять реальное подключение (не имитировать)
- Записывать аудио на всю встречу
- Создавать транскрипты
- Отправлять результаты в Telegram

**Никакого твоего участия не требуется!** 🎯
