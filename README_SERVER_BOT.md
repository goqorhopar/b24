# 🤖 Meeting Bot Server - Автоматизация встреч

Серверный бот для автоматического участия в онлайн-встречах, записи, транскрипции и анализа через AI с интеграцией в Bitrix24.

## 🚀 Возможности

- ✅ **Автоматическое присоединение** к встречам как "Асистент Григория"
- ✅ **Запись аудио** с системного звука
- ✅ **Транскрипция** через Whisper AI
- ✅ **Анализ встреч** через Gemini AI по чек-листу
- ✅ **Обновление лидов** в Bitrix24
- ✅ **Создание задач** автоматически
- ✅ **Поддержка платформ**: Zoom, Google Meet, Teams, Контур.Толк, Яндекс.Телемост
- ✅ **Серверное развертывание** без GUI

## 📋 Поддерживаемые платформы

| Платформа | Статус | Особенности |
|-----------|--------|-------------|
| **Zoom** | ✅ Полная поддержка | Автоматическое присоединение, отключение аудио/видео |
| **Google Meet** | ✅ Полная поддержка | Поддержка веб-версии |
| **Microsoft Teams** | ✅ Полная поддержка | Веб-интерфейс |
| **Контур.Толк** | ✅ Полная поддержка | Российская платформа |
| **Яндекс.Телемост** | ✅ Полная поддержка | Российская платформа |

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │───▶│  Server Meeting  │───▶│   Bitrix24      │
│                 │    │      Bot         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Gemini AI      │
                       │   (Анализ)       │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Whisper AI     │
                       │ (Транскрипция)   │
                       └──────────────────┘
```

## 🛠️ Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <your-repo>
cd b24

# Создание .env файла
cp env_example.txt .env
nano .env  # Заполните ваши данные
```

### 2. Автоматическая установка

```bash
python3 deploy_server.py
```

### 3. Ручная установка

```bash
# Системные зависимости
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git chromium-browser ffmpeg portaudio19-dev pulseaudio

# Python окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_simple.txt

# Запуск
python3 main_server_bot.py
```

### 4. Docker развертывание

```bash
# Сборка и запуск
docker build -f Dockerfile.server -t meeting-bot-server .
docker run -d --name meeting-bot -p 3000:3000 --env-file .env meeting-bot-server

# Или с docker-compose
docker-compose -f docker-compose.server.yml up -d
```

## ⚙️ Конфигурация

### Обязательные переменные

```env
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
```

### Основные настройки

```env
MEETING_DISPLAY_NAME=Асистент Григория
MEETING_DURATION_MINUTES=60
WHISPER_MODEL=base
MAX_CONCURRENT_MEETINGS=3
```

### Bitrix24 интеграция

```env
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook/
BITRIX_RESPONSIBLE_ID=1
ADMIN_CHAT_ID=your_chat_id
```

## 📱 Использование

### 1. Отправка ссылки на встречу

Просто отправьте боту ссылку на встречу:

```
https://zoom.us/j/123456789
https://meet.google.com/abc-defg-hij
https://teams.microsoft.com/l/meetup-join/...
```

### 2. Автоматический процесс

1. 🤖 Бот присоединяется как "Асистент Григория"
2. 🎙️ Начинает запись аудио
3. ⏱️ Ждет окончания встречи
4. 📝 Транскрибирует аудио
5. 🧠 Анализирует через Gemini AI
6. 📊 Отправляет результаты
7. 🔍 Запрашивает ID лида
8. 📋 Обновляет лид в Bitrix24
9. ✅ Создает задачи

### 3. Результат

```
📊 Анализ встречи завершен!

🎯 Ключевые результаты:
• Запрос: Нужна автоматизация продаж
• Проблемы: Много ручной работы
• Настроение: Заинтересованное
• Бюджет: 500,000 руб

👤 ЛПР: Найден
📅 Встреча проведена: Да

🔍 Пожалуйста, отправьте ID лида для обновления:
```

## 🔧 Системные требования

### Минимальные
- **ОС**: Ubuntu 20.04+ / CentOS 8+
- **RAM**: 4 GB
- **CPU**: 2 ядра
- **Диск**: 20 GB
- **Python**: 3.8+

### Рекомендуемые
- **ОС**: Ubuntu 22.04 LTS
- **RAM**: 8 GB
- **CPU**: 4 ядра
- **Диск**: 50 GB SSD
- **Python**: 3.10+

## 📊 Мониторинг

### Статус бота

```bash
curl http://localhost:3000/status
```

### Логи

```bash
# Systemd
sudo journalctl -u meeting-bot -f

# Docker
docker logs -f meeting-bot

# Файлы
tail -f logs/bot.log
```

### Метрики

```bash
curl http://localhost:9090/metrics
```

## 🛡️ Безопасность

### Ограничение доступа

```env
# Разрешить только определенные чаты
ALLOWED_CHAT_IDS=123456789,987654321

# Заблокировать чаты
BLOCKED_CHAT_IDS=111111111,222222222
```

### SSL/TLS

```bash
sudo certbot --nginx -d your-domain.com
```

## 🔄 Обновление

```bash
# Остановка
sudo systemctl stop meeting-bot

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install --upgrade -r requirements_simple.txt

# Запуск
sudo systemctl start meeting-bot
```

## 🐛 Устранение неполадок

### Проблемы с аудио

```bash
# Проверка устройств
arecord -l
pactl list short sinks

# Перезапуск PulseAudio
pulseaudio -k && pulseaudio --start
```

### Проблемы с браузером

```bash
# Проверка Chrome
chromium-browser --version
chromedriver --version

# Debug режим
export CHROME_HEADLESS=false
python3 main_server_bot.py
```

### Проблемы с памятью

```bash
# Мониторинг
htop
free -h

# Очистка
sudo sync && sudo echo 3 > /proc/sys/vm/drop_caches
```

## 📈 Производительность

### Оптимизация для слабых серверов

```env
WHISPER_MODEL=tiny
MAX_CONCURRENT_MEETINGS=1
MEETING_DURATION_MINUTES=30
```

### Оптимизация для мощных серверов

```env
WHISPER_MODEL=large
MAX_CONCURRENT_MEETINGS=5
MEETING_DURATION_MINUTES=120
```

## 🔗 Интеграции

### Bitrix24

- ✅ Обновление лидов
- ✅ Создание задач
- ✅ Заполнение полей
- ✅ Комментарии

### Telegram

- ✅ Получение ссылок
- ✅ Отправка результатов
- ✅ Уведомления
- ✅ Статус

### AI сервисы

- ✅ Gemini AI (анализ)
- ✅ Whisper (транскрипция)

## 📚 Документация

- [Руководство по развертыванию](SERVER_DEPLOYMENT_GUIDE.md)
- [Пример конфигурации](env_example.txt)
- [Docker развертывание](docker-compose.server.yml)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u meeting-bot -f`
2. Проверьте статус: `curl http://localhost:3000/status`
3. Проверьте конфигурацию: `python3 -c "from server_config import config; print(config.runtime_summary())"`

## 📄 Лицензия

MIT License

---

**Создано для автоматизации встреч и интеграции с Bitrix24** 🚀
