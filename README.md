# Meeting Bot

Автоматический бот для участия во встречах с записью аудио и транскрипцией.

## Возможности

- ✅ Присоединение к Google Meet, Zoom, Яндекс Телемост
- ✅ Запись только аудио (без видео)
- ✅ Транскрипция речи через Whisper
- ✅ Отправка результатов в Telegram
- ✅ Сохранение в GitHub

## Файлы

- `meeting-bot-main.py` - Основной бот (Selenium + Chrome)
- `fixed_audio_only_bot.py` - Улучшенный бот (Playwright + только аудио)
- `deploy_fixed_bot.sh` - Скрипт развертывания на сервере
- `.env` - Переменные окружения
- `server_tokens.env` - Токены для сервера

## Быстрый старт

1. Установите зависимости:
```bash
pip install python-telegram-bot selenium faster-whisper pydub speechrecognition
```

2. Настройте переменные в `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
GITHUB_TOKEN=your_token
GITHUB_REPO=your_repo
```

3. Запустите бота:
```bash
python meeting-bot-main.py
```

4. Отправьте URL встречи в Telegram

## Развертывание на сервере

```bash
chmod +x deploy_fixed_bot.sh
./deploy_fixed_bot.sh
```

## Поддерживаемые платформы

- Google Meet
- Zoom
- Яндекс Телемост
- Контур.Толк

## Требования

- Python 3.8+
- Chrome/Chromium
- PulseAudio (Linux)
- ffmpeg
- Telegram Bot Token
- GitHub Token
# Test commit for GitHub Actions
