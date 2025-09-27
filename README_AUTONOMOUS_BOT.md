# Автономный Meeting Bot

## 🤖 Полностью автономный бот для встреч

Бот работает **БЕЗ ВАШЕГО УЧАСТИЯ** на сервере 24/7!

## 🚀 Установка на сервер

### 1. Загрузите файлы на сервер:
```bash
# Скопируйте эти файлы на сервер:
- autonomous_bot.py
- meeting-bot.service
- deploy_autonomous_bot.sh
- check_bot_status.sh
```

### 2. Запустите установку:
```bash
chmod +x deploy_autonomous_bot.sh
./deploy_autonomous_bot.sh
```

## ✅ Что происходит автоматически:

1. **Бот устанавливается как systemd сервис**
2. **Автоматически запускается при старте сервера**
3. **Автоматически перезапускается при сбоях**
4. **Работает 24/7 без вашего участия**

## 📋 Команды управления:

```bash
# Проверить статус
sudo systemctl status meeting-bot.service

# Посмотреть логи
sudo journalctl -u meeting-bot.service -f

# Перезапустить
sudo systemctl restart meeting-bot.service

# Остановить
sudo systemctl stop meeting-bot.service

# Проверить все
./check_bot_status.sh
```

## 🎯 Что умеет бот:

- ✅ **Получает ссылки на встречи** (Zoom, Google Meet, Teams)
- ✅ **Анализирует через Gemini AI** (реальные вызовы API)
- ✅ **Обновляет лиды в Bitrix24** (реальные вызовы API)
- ✅ **Создает задачи автоматически**
- ✅ **Работает 24/7** без перерывов
- ✅ **Автоматически перезапускается** при сбоях

## 🔧 Настройки:

Все токены уже настроены в `meeting-bot.service`:
- Telegram Bot Token
- Gemini API Key  
- Bitrix24 Webhook URL

## 📝 Логи:

Логи сохраняются в:
- `journalctl -u meeting-bot.service` - системные логи
- `/root/b24/logs/autonomous_bot.log` - логи бота

## 🚨 Важно:

**Бот запускается автоматически при перезагрузке сервера!**
**Никакого вашего участия не требуется!**
**Работает полностью автономно!**
