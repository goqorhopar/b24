# 🤖 Meeting Bot - Автоматический бот для участия во встречах

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.15+-green.svg)](https://selenium.dev)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

Автоматический бот для участия в онлайн-встречах с записью аудио и созданием транскриптов.

## ✨ Возможности

- 🎯 **Автоматическое присоединение** к встречам на всех популярных платформах
- 🔐 **Автоматическая авторизация** - вход в закрытые встречи без ручного вмешательства
- 🎙️ **Запись аудио** на всю встречу (не ограничено 3 минутами)
- 📝 **Автоматическая транскрипция** с помощью Whisper AI
- 📤 **Отправка результатов** через Telegram
- 💾 **Сохранение в GitHub** для архивирования

## 🎮 Поддерживаемые платформы

| Платформа | Статус | Авторизация |
|-----------|--------|-------------|
| **Google Meet** | ✅ | Автоматическая |
| **Zoom** | ✅ | Автоматическая |
| **Яндекс Телемост** | ✅ | Автоматическая |
| **Контур.Толк** | ✅ | Автоматическая |
| **Microsoft Teams** | ✅ | Автоматическая |

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/goqorhopar/b24.git
cd b24
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка авторизации (один раз)
```bash
python simple_auth.py
```

### 4. Настройка переменных окружения
Создайте файл `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repo
WHISPER_MODEL=medium
RECORD_DIR=/tmp/recordings
```

### 5. Запуск бота
```bash
python meeting-bot.py
```

## 🔐 Система авторизации

### Автоматическая авторизация
Бот поддерживает автоматический вход в закрытые встречи:

```bash
# Настройка авторизации (один раз)
python simple_auth.py

# Тестирование
python test_auth.py
```

### Поддерживаемые аккаунты
- Google аккаунты (Gmail, Google Workspace)
- Zoom аккаунты (личные и корпоративные)
- Яндекс аккаунты
- Контур аккаунты
- Microsoft аккаунты (Office 365, Teams)

## 📋 Использование

### Через Telegram
1. Отправьте ссылку на встречу боту
2. Бот автоматически присоединится
3. Начнется запись аудио
4. После встречи получите транскрипт

### Поддерживаемые форматы ссылок
```
https://meet.google.com/abc-defg-hij
https://zoom.us/j/123456789
https://telemost.yandex.ru/meeting/123
https://talk.contour.ru/meeting/123
https://teams.microsoft.com/l/meetup-join/...
```

## 🛠️ Установка на сервер

### 1. Подготовка сервера
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip google-chrome-stable ffmpeg

# CentOS/RHEL
sudo yum install -y python3 python3-pip google-chrome-stable ffmpeg
```

### 2. Клонирование и настройка
```bash
git clone https://github.com/goqorhopar/b24.git
cd b24
pip3 install -r requirements.txt
```

### 3. Настройка авторизации
```bash
# На локальном компьютере
python simple_auth.py

# Скопируйте файлы на сервер
scp selenium_cookies.json storage.json user@server:/path/to/bot/
```

### 4. Запуск как сервис
```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/meeting-bot.service
```

## 📁 Структура проекта

```
b24/
├── meeting-bot.py              # Основной бот (Selenium)
├── meeting_bot_playwright.py   # Альтернативная версия (Playwright)
├── auth_platforms.py           # Полная система авторизации
├── simple_auth.py              # Простая авторизация
├── quick_auth.py               # Быстрая авторизация
├── load_auth_data.py           # Модуль загрузки данных авторизации
├── test_auth.py                # Тестирование авторизации
├── setup_auth.py               # Автоматическая установка
├── requirements.txt            # Зависимости
├── .env                        # Переменные окружения
├── .gitignore                  # Исключения для Git
└── docs/                       # Документация
    ├── AUTH_INSTRUCTIONS.md    # Инструкции по авторизации
    ├── AUTH_SETUP_GUIDE.md     # Руководство по настройке
    ├── BROWSER_FIX.md          # Исправление проблем с браузером
    └── README_AUTH.md          # Краткое руководство
```

## 🔧 Конфигурация

### Переменные окружения
| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений | - |
| `GITHUB_TOKEN` | Токен GitHub API | - |
| `GITHUB_REPO` | Репозиторий для сохранения | - |
| `WHISPER_MODEL` | Модель Whisper | `medium` |
| `RECORD_DIR` | Директория записей | `/tmp/recordings` |
| `MEETING_TIMEOUT_MIN` | Таймаут встречи (мин) | `180` |

### Модели Whisper
- `tiny` - Быстрая, низкое качество
- `base` - Баланс скорости и качества
- `small` - Хорошее качество
- `medium` - Высокое качество (рекомендуется)
- `large` - Максимальное качество

## 🐛 Устранение проблем

### Браузер не открывается
```bash
# Проверьте Chrome
google-chrome --version

# Установите зависимости
sudo apt install -y google-chrome-stable
```

### Ошибки авторизации
```bash
# Обновите авторизацию
python simple_auth.py

# Проверьте статус
python test_auth.py
```

### Проблемы с записью аудио
```bash
# Проверьте ffmpeg
ffmpeg -version

# Установите аудио драйверы
sudo apt install -y pulseaudio alsa-utils
```

## 📊 Мониторинг

### Логи
```bash
# Просмотр логов
tail -f meeting-bot.log

# Системные логи
journalctl -u meeting-bot -f
```

### Статус
```bash
# Проверка статуса бота
python -c "from load_auth_data import get_auth_loader; print(get_auth_loader().get_auth_status())"
```

## 🔒 Безопасность

- Файлы авторизации исключены из репозитория
- Используйте HTTPS для передачи данных
- Регулярно обновляйте авторизацию
- Ограничьте доступ к файлам cookies

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- 📧 Email: support@example.com
- 💬 Telegram: @meeting_bot_support
- 🐛 Issues: [GitHub Issues](https://github.com/goqorhopar/b24/issues)

## 🎯 Roadmap

- [ ] Поддержка Discord
- [ ] Веб-интерфейс
- [ ] API для интеграций
- [ ] Поддержка видео записи
- [ ] Автоматическое обновление авторизации

---

**⭐ Если проект полезен, поставьте звезду!**