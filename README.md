# Meeting Bot

Автоматический бот для участия во встречах с записью аудио и транскрипцией.

## Возможности

- ✅ Присоединение к Google Meet, Zoom, Яндекс Телемост
- ✅ Запись только аудио (без видео)
- ✅ Транскрипция речи через Whisper
- ✅ Отправка результатов в Telegram
- ✅ Сохранение в GitHub

## Быстрый старт

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные в `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
GITHUB_TOKEN=your_token
GITHUB_REPO=your_repo
```

3. Запустите бота:
```bash
python meeting-bot.py
```

4. Отправьте URL встречи в Telegram

## Поддерживаемые платформы

- Google Meet
- Zoom
- Яндекс Телемост

## Требования

- Python 3.8+
- Chrome/Chromium
- PulseAudio (Linux)
- ffmpeg
- Telegram Bot Token
- GitHub Token
