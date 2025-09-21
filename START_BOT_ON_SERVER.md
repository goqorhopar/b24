# 🚀 ЗАПУСК БОТА НА СЕРВЕРЕ

## ⚠️ ВАЖНО: Бот должен работать ТОЛЬКО на Linux сервере!

### 1. Подключитесь к серверу по SSH:
```bash
ssh ваш_пользователь@ваш_сервер_ip
```

### 2. Перейдите в папку с ботом:
```bash
cd /path/to/your/bot/folder
```

### 3. Убедитесь, что .env файл настроен:
```bash
cat .env
```

### 4. Запустите бота:
```bash
# Вариант 1: Простой запуск
python3 start_bot_fixed.py

# Вариант 2: Запуск в фоне
nohup python3 start_bot_fixed.py > bot.log 2>&1 &

# Вариант 3: Через systemd (рекомендуется)
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

### 5. Проверьте, что бот работает:
```bash
# Проверка процессов
ps aux | grep python

# Проверка логов
tail -f bot.log

# Или если через systemd:
sudo systemctl status telegram-bot
```

### 6. Тестирование в Telegram:
1. Найдите бота: @TranscriptionleadBot
2. Отправьте команду: `/start`
3. Отправьте ссылку на встречу

## 🔧 Если бот не запускается:

### Проверьте зависимости:
```bash
pip3 install -r requirements.txt
```

### Проверьте права доступа:
```bash
chmod +x start_bot_fixed.py
chmod +x deploy_to_server.sh
```

### Проверьте логи:
```bash
tail -f bot.log
```

## 📱 Тестирование функционала:

1. **Отправьте ссылку на встречу** (Zoom, Google Meet, Teams)
2. **Бот должен:**
   - ✅ Присоединиться к встрече
   - ✅ Записать аудио
   - ✅ Сделать транскрипцию
   - ✅ Проанализировать через Gemini
   - ✅ Отправить результат в чат
   - ✅ Попросить ID лида в Bitrix
   - ✅ Обновить лид в Bitrix

## 🆘 Если что-то не работает:

1. Проверьте логи: `tail -f bot.log`
2. Проверьте статус: `sudo systemctl status telegram-bot`
3. Перезапустите: `sudo systemctl restart telegram-bot`

---

**ПОМНИТЕ: Бот работает ТОЛЬКО на Linux сервере!**
