# 🚀 Инструкция по развертыванию бота на Linux сервере

## ⚠️ ВАЖНО: Бот должен работать ТОЛЬКО на Linux сервере!

### 📋 Требования к серверу:

- **ОС:** Ubuntu 20.04+ или Debian 11+
- **RAM:** минимум 2GB, рекомендуется 4GB+
- **CPU:** минимум 2 ядра
- **Диск:** минимум 10GB свободного места
- **Интернет:** стабильное соединение

### 🔧 Подготовка сервера:

#### 1. Подключение к серверу:
```bash
ssh root@your-server-ip
# или
ssh user@your-server-ip
```

#### 2. Загрузка файлов бота:
```bash
# Создайте директорию для бота
mkdir -p /tmp/meeting-bot
cd /tmp/meeting-bot

# Загрузите все файлы бота на сервер
# (используйте scp, rsync или git clone)
```

#### 3. Запуск развертывания:
```bash
# Сделайте скрипт исполняемым
chmod +x deploy_to_server.sh

# Запустите развертывание
sudo ./deploy_to_server.sh
```

### 🎯 Что делает скрипт развертывания:

1. **✅ Обновляет систему**
2. **✅ Устанавливает Python 3 и pip**
3. **✅ Устанавливает системные зависимости:**
   - PulseAudio (для записи аудио)
   - FFmpeg (для обработки аудио)
   - Chrome/Chromium (для автоматизации)
   - ChromeDriver (для Selenium)
   - X11 (для виртуального дисплея)

4. **✅ Создает пользователя `bot`**
5. **✅ Устанавливает Python зависимости**
6. **✅ Создает systemd сервис**
7. **✅ Настраивает автозапуск**
8. **✅ Запускает бота**

### 🛠 Управление ботом на сервере:

#### Команды управления:
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

# Включить автозапуск
sudo /opt/meeting-bot/manage_bot.sh enable

# Отключить автозапуск
sudo /opt/meeting-bot/manage_bot.sh disable
```

#### Альтернативные команды systemd:
```bash
# Запуск
sudo systemctl start meeting-bot

# Остановка
sudo systemctl stop meeting-bot

# Перезапуск
sudo systemctl restart meeting-bot

# Статус
sudo systemctl status meeting-bot

# Логи
sudo journalctl -u meeting-bot -f

# Включить автозапуск
sudo systemctl enable meeting-bot

# Отключить автозапуск
sudo systemctl disable meeting-bot
```

### 📊 Мониторинг работы:

#### Проверка статуса:
```bash
# Статус сервиса
sudo systemctl status meeting-bot

# Процессы Python
ps aux | grep python

# Использование ресурсов
htop
# или
top
```

#### Просмотр логов:
```bash
# Логи systemd
sudo journalctl -u meeting-bot -f

# Логи бота
tail -f /opt/meeting-bot/bot.log

# Все логи
sudo journalctl -u meeting-bot --since "1 hour ago"
```

### 🔍 Диагностика проблем:

#### Бот не запускается:
```bash
# Проверьте статус
sudo systemctl status meeting-bot

# Проверьте логи
sudo journalctl -u meeting-bot -n 50

# Проверьте зависимости
sudo /opt/meeting-bot/venv/bin/python -c "import flask, selenium, whisper"
```

#### Проблемы с аудио:
```bash
# Проверьте PulseAudio
pulseaudio --check -v

# Список аудиоустройств
pactl list sources short

# Тест записи
parecord --device=0 test.wav
```

#### Проблемы с Chrome:
```bash
# Проверьте Chrome
google-chrome --version

# Проверьте ChromeDriver
chromedriver --version

# Тест Chrome
google-chrome --headless --no-sandbox --disable-dev-shm-usage
```

### 🔒 Безопасность:

#### Настройка файрвола:
```bash
# Разрешить SSH
sudo ufw allow ssh

# Разрешить HTTP (если нужен)
sudo ufw allow 80
sudo ufw allow 443

# Включить файрвол
sudo ufw enable
```

#### Настройка пользователя:
```bash
# Создать пользователя для администрирования
sudo adduser admin
sudo usermod -aG sudo admin

# Отключить root SSH (опционально)
sudo nano /etc/ssh/sshd_config
# Установить PermitRootLogin no
sudo systemctl restart ssh
```

### 📈 Масштабирование:

#### Для высоких нагрузок:
```bash
# Увеличить лимиты системы
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Настроить swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 🚨 Важные замечания:

1. **❌ НЕ запускайте бота на Windows ноуте!**
2. **✅ Бот должен работать ТОЛЬКО на Linux сервере!**
3. **🔒 Регулярно обновляйте систему**
4. **📊 Мониторьте использование ресурсов**
5. **💾 Делайте резервные копии конфигурации**

### 📞 Поддержка:

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u meeting-bot -f`
2. Проверьте статус: `sudo systemctl status meeting-bot`
3. Проверьте зависимости: `sudo /opt/meeting-bot/venv/bin/python -c "import flask, selenium, whisper"`
4. Перезапустите бота: `sudo systemctl restart meeting-bot`

---

**🎯 Цель:** Бот должен работать 24/7 на Linux сервере!  
**❌ Запрещено:** Запуск на Windows ноуте!  
**✅ Разрешено:** Только Linux сервер!
