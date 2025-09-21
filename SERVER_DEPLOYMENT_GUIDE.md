# Руководство по развертыванию Meeting Bot на сервере

## Обзор

Этот бот автоматически подключается к встречам как "Асистент Григория", записывает аудио, транскрибирует и анализирует встречи через Gemini AI, а затем обновляет лиды в Bitrix24.

## Поддерживаемые платформы

- ✅ Zoom
- ✅ Google Meet  
- ✅ Microsoft Teams
- ✅ Контур.Толк
- ✅ Яндекс.Телемост

## Системные требования

### Минимальные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 4 GB
- **CPU**: 2 ядра
- **Диск**: 20 GB свободного места
- **Python**: 3.8+

### Рекомендуемые требования
- **ОС**: Ubuntu 22.04 LTS
- **RAM**: 8 GB
- **CPU**: 4 ядра
- **Диск**: 50 GB SSD
- **Python**: 3.10+

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <your-repo-url>
cd b24
```

### 2. Настройка переменных окружения

Создайте файл `.env`:

```bash
cp .env.example .env
nano .env
```

Заполните обязательные переменные:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Bitrix24 (опционально)
BITRIX_WEBHOOK_URL=your_bitrix_webhook_url_here
BITRIX_RESPONSIBLE_ID=1

# Admin
ADMIN_CHAT_ID=your_admin_chat_id_here
```

### 3. Автоматическая установка

```bash
python3 deploy_server.py
```

### 4. Ручная установка

```bash
# Установка системных зависимостей
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git chromium-browser ffmpeg portaudio19-dev pulseaudio

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
pip install -r requirements_simple.txt

# Запуск бота
python3 main_server_bot.py
```

## Развертывание с Docker

### 1. Сборка образа

```bash
docker build -f Dockerfile.server -t meeting-bot-server .
```

### 2. Запуск контейнера

```bash
docker run -d \
  --name meeting-bot \
  --restart unless-stopped \
  -p 3000:3000 \
  -p 9090:9090 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/tmp/meeting_bot \
  --privileged \
  meeting-bot-server
```

### 3. Использование docker-compose

```bash
docker-compose -f docker-compose.server.yml up -d
```

## Настройка systemd сервиса

### 1. Создание сервиса

```bash
sudo nano /etc/systemd/system/meeting-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=Meeting Bot Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/your/bot
Environment=PATH=/path/to/your/bot/venv/bin
ExecStart=/path/to/your/bot/venv/bin/python main_server_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Активация сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable meeting-bot
sudo systemctl start meeting-bot
```

### 3. Проверка статуса

```bash
sudo systemctl status meeting-bot
sudo journalctl -u meeting-bot -f
```

## Настройка аудиосистемы

### 1. Создание виртуального аудиоустройства

```bash
# Создание null sink для записи
pactl load-module module-null-sink sink_name=meeting_bot

# Создание loopback для захвата системного звука
pactl load-module module-loopback source=meeting_bot.monitor sink=@DEFAULT_SINK@

# Установка как устройство по умолчанию
pactl set-default-source meeting_bot.monitor
```

### 2. Проверка аудиоустройств

```bash
# Список устройств
pactl list short sinks
pactl list short sources

# Тест записи
arecord -f cd -t wav -d 5 test.wav
```

## Настройка файрвола

```bash
# Разрешение портов
sudo ufw allow 3000/tcp  # Основной порт бота
sudo ufw allow 9090/tcp  # Метрики
sudo ufw allow ssh       # SSH

# Включение файрвола
sudo ufw enable
```

## Мониторинг и логирование

### 1. Просмотр логов

```bash
# Логи systemd сервиса
sudo journalctl -u meeting-bot -f

# Логи приложения
tail -f logs/bot.log

# Логи Docker
docker logs -f meeting-bot
```

### 2. Проверка статуса

```bash
# HTTP статус
curl http://localhost:3000/status

# Проверка процессов
ps aux | grep python
```

### 3. Метрики (если включены)

```bash
# Prometheus метрики
curl http://localhost:9090/metrics
```

## Конфигурация

### Основные параметры

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `MEETING_DISPLAY_NAME` | Имя в встречах | "Асистент Григория" |
| `MEETING_DURATION_MINUTES` | Максимальная длительность встречи | 60 |
| `WHISPER_MODEL` | Модель Whisper | "base" |
| `MAX_CONCURRENT_MEETINGS` | Максимум одновременных встреч | 3 |
| `AUDIO_RECORDING_METHOD` | Метод записи аудио | "auto" |

### Настройки производительности

```env
# Для слабых серверов
WHISPER_MODEL=tiny
MAX_CONCURRENT_MEETINGS=1
MEETING_DURATION_MINUTES=30

# Для мощных серверов
WHISPER_MODEL=large
MAX_CONCURRENT_MEETINGS=5
MEETING_DURATION_MINUTES=120
```

## Устранение неполадок

### Проблемы с аудио

```bash
# Проверка аудиоустройств
arecord -l
aplay -l

# Перезапуск PulseAudio
pulseaudio -k
pulseaudio --start

# Проверка модулей
pactl list modules short
```

### Проблемы с браузером

```bash
# Проверка Chrome/Chromium
chromium-browser --version
chromedriver --version

# Запуск в debug режиме
export CHROME_HEADLESS=false
python3 main_server_bot.py
```

### Проблемы с памятью

```bash
# Мониторинг памяти
free -h
htop

# Очистка кэша
sudo sync
sudo echo 3 > /proc/sys/vm/drop_caches
```

### Проблемы с сетью

```bash
# Проверка подключения
ping google.com
curl -I https://api.telegram.org

# Проверка портов
netstat -tlnp | grep :3000
```

## Безопасность

### 1. Ограничение доступа

```env
# Разрешить только определенные чаты
ALLOWED_CHAT_IDS=123456789,987654321

# Заблокировать чаты
BLOCKED_CHAT_IDS=111111111,222222222
```

### 2. SSL/TLS

```bash
# Установка SSL сертификата
sudo certbot --nginx -d your-domain.com
```

### 3. Обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade

# Обновление зависимостей
pip install --upgrade -r requirements_simple.txt
```

## Резервное копирование

### 1. Конфигурация

```bash
# Создание бэкапа
tar -czf bot-config-backup-$(date +%Y%m%d).tar.gz .env logs/
```

### 2. Автоматический бэкап

```bash
# Добавить в crontab
0 2 * * * /path/to/backup-script.sh
```

## Масштабирование

### Горизонтальное масштабирование

```yaml
# docker-compose.yml
services:
  meeting-bot-1:
    # ... конфигурация
  meeting-bot-2:
    # ... конфигурация
  nginx:
    # Load balancer
```

### Вертикальное масштабирование

```env
# Увеличение лимитов
MAX_CONCURRENT_MEETINGS=10
MEETING_TIMEOUT_SECONDS=7200
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u meeting-bot -f`
2. Проверьте статус: `curl http://localhost:3000/status`
3. Проверьте конфигурацию: `python3 -c "from server_config import config; print(config.runtime_summary())"`

## Лицензия

MIT License