# 🚀 Быстрое исправление автоматизации встреч

## Проблема
Бот не присоединяется к встречам автоматически.

## Решение (выполните на VPS)

### Шаг 1: Подключитесь к VPS
```bash
ssh root@109.172.47.253
```

### Шаг 2: Выполните команды исправления
```bash
cd /opt/telegram-bot

# Скачиваем и запускаем скрипт исправления
wget https://raw.githubusercontent.com/goqorhopar/b24/main/fix_meeting_automation.sh
chmod +x fix_meeting_automation.sh
./fix_meeting_automation.sh
```

### Шаг 3: Проверьте работу
```bash
# Смотрите логи в реальном времени
journalctl -u telegram-bot -f
```

### Шаг 4: Тестируйте бота
1. Отправьте боту команду `/start`
2. Отправьте ссылку на встречу (например: `https://2a14p7ld.ktalk.ru/r38minvlcc6e`)
3. Бот должен ответить: "🚀 Получил ссылку на встречу! Начинаю процесс автоматического присоединения..."

## Если что-то не работает

### Диагностика:
```bash
# Запустите диагностический скрипт
wget https://raw.githubusercontent.com/goqorhopar/b24/main/diagnose_bot.sh
chmod +x diagnose_bot.sh
./diagnose_bot.sh
```

### Ручное исправление:
```bash
# 1. Остановите бота
systemctl stop telegram-bot

# 2. Установите виртуальный дисплей
apt update
apt install -y xvfb x11vnc fluxbox firefox-esr chromium-browser pulseaudio alsa-utils

# 3. Обновите код
cd /opt/telegram-bot
git pull origin main
cp main_with_meeting_automation.py main.py

# 4. Создайте скрипт запуска
cat > start_with_display.sh << 'EOF'
#!/bin/bash
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!
DISPLAY=:99 fluxbox > /dev/null 2>&1 &
FLUXBOX_PID=$!
pulseaudio --start --exit-idle-time=-1 > /dev/null 2>&1 &
sleep 3
cd /opt/telegram-bot
source venv/bin/activate
python main.py
kill $XVFB_PID $FLUXBOX_PID 2>/dev/null
EOF
chmod +x start_with_display.sh

# 5. Обновите systemd сервис
cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Bot with Virtual Display
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
Environment=DISPLAY=:99
ExecStart=/opt/telegram-bot/start_with_display.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Перезапустите бота
systemctl daemon-reload
systemctl start telegram-bot
systemctl status telegram-bot
```

## Что должно произойти

После исправления бот будет:
- ✅ Автоматически присоединяться к встречам
- ✅ Записывать аудио
- ✅ Анализировать контент
- ✅ Обновлять лиды в Bitrix24

## Поддерживаемые платформы

- Zoom (zoom.us)
- Google Meet (meet.google.com) 
- Microsoft Teams (teams.microsoft.com)
- Контур.Толк (ktalk.ru, talk.kontur.ru, 2a14p7ld.ktalk.ru)
- Яндекс Телемост (telemost.yandex.ru)

## Контакты

Если проблемы остаются, проверьте:
1. Логи бота: `journalctl -u telegram-bot -f`
2. Статус сервиса: `systemctl status telegram-bot`
3. Диагностику: `./diagnose_bot.sh`
