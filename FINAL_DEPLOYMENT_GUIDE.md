# 🚀 ФИНАЛЬНАЯ ИНСТРУКЦИЯ: Развертывание бота на Linux сервере

## ⚠️ КРИТИЧЕСКИ ВАЖНО:
- **❌ БОТ НЕ ДОЛЖЕН РАБОТАТЬ НА WINDOWS НОУТЕ!**
- **✅ БОТ ДОЛЖЕН РАБОТАТЬ ТОЛЬКО НА LINUX СЕРВЕРЕ!**
- **🔄 БОТ ДОЛЖЕН РАБОТАТЬ 24/7 НА СЕРВЕРЕ!**

## 📋 Что у вас есть:

### ✅ Готовые файлы:
- `deploy_to_server.sh` - скрипт автоматического развертывания
- `upload_to_server.sh` - скрипт загрузки файлов на сервер
- `SERVER_DEPLOYMENT_INSTRUCTIONS.md` - подробная инструкция
- Все модули бота готовы к работе

### ✅ Настройки бота:
- **Telegram:** @TranscriptionleadBot (7992998044)
- **Gemini API:** AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
- **Bitrix24:** https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31
- **Admin Chat ID:** 7537953397

## 🚀 Пошаговое развертывание:

### Шаг 1: Подготовка сервера
```bash
# Подключитесь к вашему Linux серверу
ssh root@your-server-ip
# или
ssh user@your-server-ip
```

### Шаг 2: Загрузка файлов
```bash
# На Windows ноуте выполните:
chmod +x upload_to_server.sh
./upload_to_server.sh

# Или загрузите файлы вручную через scp/rsync
```

### Шаг 3: Развертывание
```bash
# На сервере выполните:
cd /tmp/meeting-bot
chmod +x deploy_to_server.sh
sudo ./deploy_to_server.sh
```

### Шаг 4: Проверка
```bash
# Проверьте статус бота:
sudo systemctl status meeting-bot

# Проверьте логи:
sudo journalctl -u meeting-bot -f
```

## 🛠 Управление ботом на сервере:

### Основные команды:
```bash
# Запуск бота
sudo /opt/meeting-bot/manage_bot.sh start

# Остановка бота
sudo /opt/meeting-bot/manage_bot.sh stop

# Перезапуск бота
sudo /opt/meeting-bot/manage_bot.sh restart

# Статус бота
sudo /opt/meeting-bot/manage_bot.sh status

# Просмотр логов
sudo /opt/meeting-bot/manage_bot.sh logs
```

### Проверка работы:
```bash
# Статус сервиса
sudo systemctl status meeting-bot

# Процессы
ps aux | grep python

# Логи в реальном времени
sudo journalctl -u meeting-bot -f
```

## 🧪 Тестирование бота:

### В Telegram:
1. **Найдите бота:** @TranscriptionleadBot
2. **Отправьте команду:** `/start`
3. **Отправьте ссылку на встречу:** `https://zoom.us/j/123456789`
4. **Бот должен:**
   - ✅ Определить платформу (Zoom)
   - ✅ Присоединиться к встрече
   - ✅ Записать аудио
   - ✅ Транскрибировать речь
   - ✅ Проанализировать через Gemini
   - ✅ Отправить анализ в чат
   - ✅ Запросить ID лида
   - ✅ Обновить лид в Bitrix24

## 🔧 Что делает скрипт развертывания:

1. **✅ Обновляет систему Ubuntu/Debian**
2. **✅ Устанавливает Python 3 и pip**
3. **✅ Устанавливает системные зависимости:**
   - PulseAudio (для записи аудио)
   - FFmpeg (для обработки аудио)
   - Chrome/Chromium (для автоматизации)
   - ChromeDriver (для Selenium)
   - X11 (для виртуального дисплея)

4. **✅ Создает пользователя `bot`**
5. **✅ Устанавливает Python зависимости**
6. **✅ Создает systemd сервис для автозапуска**
7. **✅ Настраивает PulseAudio для записи аудио**
8. **✅ Запускает бота**

## 📊 Мониторинг:

### Проверка статуса:
```bash
# Статус бота
sudo systemctl status meeting-bot

# Использование ресурсов
htop

# Логи
sudo journalctl -u meeting-bot -f
```

### Автоматический перезапуск:
```bash
# Бот автоматически перезапускается при сбоях
# Проверьте настройки в systemd
sudo systemctl show meeting-bot | grep Restart
```

## 🚨 Важные замечания:

### ❌ НЕ ДЕЛАЙТЕ:
- Не запускайте бота на Windows ноуте
- Не изменяйте настройки без необходимости
- Не удаляйте пользователя `bot`

### ✅ ДЕЛАЙТЕ:
- Регулярно проверяйте статус бота
- Мониторьте логи на предмет ошибок
- Делайте резервные копии конфигурации
- Обновляйте систему сервера

## 🔍 Диагностика проблем:

### Бот не запускается:
```bash
# Проверьте логи
sudo journalctl -u meeting-bot -n 50

# Проверьте зависимости
sudo /opt/meeting-bot/venv/bin/python -c "import flask, selenium, whisper"

# Перезапустите
sudo systemctl restart meeting-bot
```

### Проблемы с аудио:
```bash
# Проверьте PulseAudio
pulseaudio --check -v

# Список устройств
pactl list sources short

# Тест записи
parecord --device=0 test.wav
```

### Проблемы с Chrome:
```bash
# Проверьте Chrome
google-chrome --version

# Проверьте ChromeDriver
chromedriver --version
```

## 📞 Поддержка:

### При возникновении проблем:
1. **Проверьте логи:** `sudo journalctl -u meeting-bot -f`
2. **Проверьте статус:** `sudo systemctl status meeting-bot`
3. **Перезапустите бота:** `sudo systemctl restart meeting-bot`
4. **Проверьте зависимости:** `sudo /opt/meeting-bot/venv/bin/python -c "import flask, selenium, whisper"`

### Контакты:
- **Telegram:** @TranscriptionleadBot
- **Admin Chat ID:** 7537953397

---

## 🎯 ИТОГ:

**✅ Бот полностью готов к развертыванию на Linux сервере!**

**📋 Следующие шаги:**
1. Подключитесь к Linux серверу
2. Загрузите файлы бота
3. Запустите `deploy_to_server.sh`
4. Проверьте работу бота
5. Протестируйте в Telegram

**🚀 Бот будет работать 24/7 на сервере и автоматически обрабатывать встречи!**

---

**Версия:** 1.0.0  
**Статус:** ✅ Готов к продакшену на Linux сервере  
**Цель:** 24/7 работа на сервере, НЕ на ноуте!
