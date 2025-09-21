# 🚀 Быстрый старт Meeting Bot Server

## Что делает бот

1. **Получает ссылку на встречу** в Telegram
2. **Автоматически присоединяется** как "Асистент Григория"
3. **Записывает аудио** встречи
4. **Транскрибирует** через Whisper AI
5. **Анализирует** через Gemini AI по чек-листу
6. **Отправляет результаты** в чат
7. **Запрашивает ID лида**
8. **Обновляет лид** в Bitrix24
9. **Создает задачи** автоматически

## ⚡ Быстрый запуск (5 минут)

### 1. Подготовка

```bash
# Клонирование
git clone <your-repo>
cd b24

# Создание .env
cp env_example.txt .env
nano .env  # Заполните TELEGRAM_BOT_TOKEN и GEMINI_API_KEY
```

### 2. Автоматическая установка

```bash
python3 deploy_server.py
```

### 3. Запуск

```bash
python3 main_server_bot.py
```

## 🔧 Ручная установка

### Ubuntu/Debian

```bash
# Системные пакеты
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git chromium-browser ffmpeg portaudio19-dev pulseaudio

# Python окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_simple.txt

# Запуск
python3 main_server_bot.py
```

### CentOS/RHEL

```bash
# Системные пакеты
sudo yum update -y
sudo yum install -y python3-pip python3-venv git chromium ffmpeg portaudio-devel pulseaudio

# Python окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_simple.txt

# Запуск
python3 main_server_bot.py
```

## 🐳 Docker запуск

```bash
# Сборка
docker build -f Dockerfile.server -t meeting-bot-server .

# Запуск
docker run -d \
  --name meeting-bot \
  -p 3000:3000 \
  --env-file .env \
  meeting-bot-server
```

## 📱 Использование

### 1. Отправьте боту ссылку на встречу

```
https://zoom.us/j/123456789
https://meet.google.com/abc-defg-hij
https://teams.microsoft.com/l/meetup-join/...
```

### 2. Бот автоматически:

- ✅ Присоединится как "Асистент Григория"
- ✅ Запишет встречу
- ✅ Проанализирует через AI
- ✅ Отправит результаты

### 3. Введите ID лида

```
12345
```

### 4. Бот обновит лид в Bitrix24

## ⚙️ Минимальная конфигурация

Создайте файл `.env`:

```env
# ОБЯЗАТЕЛЬНО
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here

# ОПЦИОНАЛЬНО
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook/
ADMIN_CHAT_ID=your_chat_id_here
```

## 🔍 Проверка работы

### Тест системы

```bash
python3 test_server_bot.py
```

### Проверка статуса

```bash
curl http://localhost:3000/status
```

### Просмотр логов

```bash
tail -f logs/bot.log
```

## 🛠️ Устранение проблем

### Проблема: "Не удалось присоединиться к встрече"

**Решение:**
```bash
# Проверьте Chrome
chromium-browser --version

# Проверьте права
sudo chmod +x /usr/bin/chromedriver
```

### Проблема: "Не удалось записать аудио"

**Решение:**
```bash
# Проверьте аудиоустройства
arecord -l

# Перезапустите PulseAudio
pulseaudio -k && pulseaudio --start
```

### Проблема: "Gemini API ошибка"

**Решение:**
```bash
# Проверьте API ключ
echo $GEMINI_API_KEY

# Проверьте интернет
curl -I https://generativelanguage.googleapis.com
```

## 📊 Мониторинг

### Статус бота

```bash
curl http://localhost:3000/status
```

### Логи в реальном времени

```bash
tail -f logs/bot.log
```

### Системные ресурсы

```bash
htop
free -h
```

## 🔄 Обновление

```bash
# Остановка
pkill -f main_server_bot.py

# Обновление
git pull origin main
pip install --upgrade -r requirements_simple.txt

# Запуск
python3 main_server_bot.py
```

## 🆘 Поддержка

### Логи ошибок

```bash
# Последние ошибки
grep ERROR logs/bot.log | tail -20

# Все логи
cat logs/bot.log
```

### Проверка конфигурации

```bash
python3 -c "
from server_config import config
print('Config OK:', config.validate())
print('Display Name:', config.MEETING_DISPLAY_NAME)
"
```

### Тест компонентов

```bash
# Тест всех компонентов
python3 test_server_bot.py

# Тест только Gemini
python3 -c "from gemini_client import test_gemini_connection; print(test_gemini_connection())"

# Тест только Bitrix
python3 -c "from bitrix import test_bitrix_connection; print(test_bitrix_connection())"
```

## 📋 Чек-лист запуска

- [ ] Python 3.8+ установлен
- [ ] Chrome/Chromium установлен
- [ ] FFmpeg установлен
- [ ] PulseAudio работает
- [ ] .env файл создан
- [ ] TELEGRAM_BOT_TOKEN заполнен
- [ ] GEMINI_API_KEY заполнен
- [ ] Зависимости установлены
- [ ] Тест пройден
- [ ] Бот запущен

## 🎯 Готово!

После выполнения всех шагов ваш бот готов к работе:

1. **Отправьте ссылку на встречу** боту в Telegram
2. **Бот присоединится** автоматически
3. **Получите анализ** встречи
4. **Введите ID лида** для обновления
5. **Лид обновится** в Bitrix24

**Удачного использования! 🚀**
