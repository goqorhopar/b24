# 🚀 ФИНАЛЬНЫЕ ИНСТРУКЦИИ ДЛЯ ДЕПЛОЯ

## 📦 Файл готов: `bot_deploy.zip` (240 KB)

---

## 🔥 БЫСТРЫЙ ДЕПЛОЙ:

### 1. Загрузите архив на сервер:
```bash
# Через SCP (замените на ваши данные)
scp bot_deploy.zip ваш_пользователь@ваш_сервер_ip:/home/ваш_пользователь/

# Или через SFTP, или загрузите через веб-интерфейс
```

### 2. Подключитесь к серверу:
```bash
ssh ваш_пользователь@ваш_сервер_ip
```

### 3. Распакуйте и запустите:
```bash
# Распакуйте архив
unzip bot_deploy.zip

# Сделайте скрипт исполняемым
chmod +x quick_start_server.sh

# Запустите бота
./quick_start_server.sh
```

### 4. Проверьте работу:
```bash
# Проверьте процессы
ps aux | grep python

# Проверьте логи
tail -f bot.log

# Проверьте статус
sudo systemctl status telegram-bot
```

---

## 🧪 ТЕСТИРОВАНИЕ:

1. **Найдите бота:** @TranscriptionleadBot
2. **Отправьте:** `/start`
3. **Отправьте ссылку на встречу:**
   - Zoom: `https://zoom.us/j/123456789`
   - Google Meet: `https://meet.google.com/abc-defg-hij`
   - Teams: `https://teams.microsoft.com/l/meetup-join/...`
   - Яндекс Телемост: `https://telemost.yandex.ru/j/123456789`

---

## ✅ ЧТО ДОЛЖНО ПРОИЗОЙТИ:

1. **Бот присоединится к встрече** (откроет браузер)
2. **Запишет аудио** встречи
3. **Сделает транскрипцию** через Whisper
4. **Проанализирует** через Gemini AI
5. **Отправит результат** в Telegram чат
6. **Попросит ID лида** в Bitrix
7. **Обновит лид** в Bitrix24

---

## 🆘 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ:

### Проверьте логи:
```bash
tail -f bot.log
```

### Перезапустите бота:
```bash
pkill -f python
./quick_start_server.sh
```

### Проверьте зависимости:
```bash
pip3 install -r requirements.txt
```

---

## 📞 ПОДДЕРЖКА:

- **Бот:** @TranscriptionleadBot
- **Логи:** `tail -f bot.log`
- **Статус:** `ps aux | grep python`

---

**🎯 БОТ ГОТОВ К РАБОТЕ НА СЕРВЕРЕ!**
