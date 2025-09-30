# 🚀 Развертывание Meeting Bot на сервере

## ✅ Да, бот вспомнит авторизацию!

Если у вас есть файлы авторизации, бот автоматически будет использовать их на сервере.

## 📋 Что нужно для развертывания

### 1. Файлы авторизации (у вас уже есть)
```
selenium_cookies.json     # Основные cookies
storage.json             # Storage данные
cookies_google_meet.json # Google Meet cookies
cookies_microsoft_teams.json # Teams cookies
storage_zoom.json        # Zoom storage
```

### 2. Копирование файлов на сервер

#### Вариант 1: SCP (рекомендуется)
```bash
# Скопируйте файлы авторизации на сервер
scp selenium_cookies.json user@server:/path/to/bot/
scp storage.json user@server:/path/to/bot/
scp cookies_*.json user@server:/path/to/bot/
scp storage_*.json user@server:/path/to/bot/
```

#### Вариант 2: SFTP
```bash
sftp user@server
put selenium_cookies.json
put storage.json
put cookies_*.json
put storage_*.json
```

#### Вариант 3: Git (НЕ рекомендуется для cookies)
```bash
# НЕ делайте это - файлы cookies не должны быть в Git!
# git add cookies*.json  # ❌ ОШИБКА!
```

## 🔧 Настройка сервера

### 1. Установка зависимостей
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip google-chrome-stable ffmpeg

# CentOS/RHEL
sudo yum install -y python3 python3-pip google-chrome-stable ffmpeg
```

### 2. Клонирование репозитория
```bash
git clone https://github.com/goqorhopar/b24.git
cd b24
pip3 install -r requirements.txt
```

### 3. Копирование файлов авторизации
```bash
# Скопируйте файлы авторизации в директорию бота
cp /path/to/your/cookies/*.json ./
```

### 4. Настройка переменных окружения
```bash
nano .env
```

Содержимое `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repo
WHISPER_MODEL=medium
RECORD_DIR=/tmp/recordings
MEETING_TIMEOUT_MIN=180
```

## 🧪 Тестирование авторизации

### Проверка файлов
```bash
# Проверьте, что файлы на месте
ls -la *.json

# Должны быть:
# selenium_cookies.json
# storage.json
# cookies_*.json
# storage_*.json
```

### Тестирование системы
```bash
python3 test_auth.py
```

Ожидаемый результат:
```
✅ Полная авторизация доступна
```

## 🚀 Запуск бота

### Ручной запуск
```bash
python3 meeting-bot.py
```

### Запуск как сервис
```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/meeting-bot.service
```

Содержимое сервиса:
```ini
[Unit]
Description=Meeting Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 meeting-bot.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/path/to/bot

[Install]
WantedBy=multi-user.target
```

Активация сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable meeting-bot
sudo systemctl start meeting-bot
```

## 🔍 Проверка работы

### Логи сервиса
```bash
sudo journalctl -u meeting-bot -f
```

### Статус сервиса
```bash
sudo systemctl status meeting-bot
```

### Проверка авторизации
```bash
python3 -c "from load_auth_data import get_auth_loader; print(get_auth_loader().get_auth_status())"
```

## 🎯 Что произойдет при запуске

1. **Бот загрузит файлы авторизации**
2. **Применит cookies к браузеру**
3. **Сможет входить в закрытые встречи**
4. **Автоматически присоединяться к встречам**

### Логи при успешной авторизации:
```
✅ Загружены Selenium cookies: 45 записей
✅ Применены storage данные
✅ Драйвер настроен с авторизацией
```

## 🔄 Обновление авторизации

### Если cookies истекли:
```bash
# На локальном компьютере
python simple_auth.py

# Скопируйте новые файлы на сервер
scp selenium_cookies.json user@server:/path/to/bot/
scp storage.json user@server:/path/to/bot/
```

## 🛠️ Устранение проблем

### Проблема: "Авторизация не настроена"
```bash
# Проверьте файлы
ls -la *.json

# Если файлов нет, скопируйте их
scp /path/to/local/cookies/*.json ./
```

### Проблема: "Cookies не применяются"
```bash
# Проверьте права доступа
chmod 644 *.json

# Проверьте содержимое файлов
head -5 selenium_cookies.json
```

### Проблема: "Браузер не открывается"
```bash
# Установите Chrome
sudo apt install -y google-chrome-stable

# Проверьте версию
google-chrome --version
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус авторизации
python3 -c "from load_auth_data import get_auth_loader; print(get_auth_loader().get_auth_status())"

# Статус сервиса
sudo systemctl status meeting-bot

# Логи
sudo journalctl -u meeting-bot --since "1 hour ago"
```

## ✅ Итог

**Да, бот вспомнит авторизацию на сервере!**

Просто скопируйте файлы авторизации на сервер, и бот будет автоматически:
- ✅ Входить в Google Meet
- ✅ Входить в Zoom
- ✅ Входить в Яндекс Телемост
- ✅ Входить в Контур.Толк
- ✅ Входить в Microsoft Teams

**Главное:** Файлы cookies должны быть на сервере в той же директории, где запускается бот!
