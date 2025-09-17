# Настройка автоматизации встреч на VPS

## Проблема
Бот не может автоматически присоединяться к встречам, потому что на VPS нет графического интерфейса, а модули автоматизации (pyautogui, selenium) требуют дисплей.

## Решение

### Вариант 1: Быстрое исправление (рекомендуется)

1. **Подключитесь к VPS:**
```bash
ssh root@109.172.47.253
```

2. **Выполните установку виртуального дисплея:**
```bash
cd /opt/telegram-bot
wget https://raw.githubusercontent.com/your-repo/b24/main/vps_setup_with_gui.sh
chmod +x vps_setup_with_gui.sh
./vps_setup_with_gui.sh
```

3. **Замените main.py на версию с автоматизацией:**
```bash
cp main.py main.py.backup
wget https://raw.githubusercontent.com/your-repo/b24/main/main_with_meeting_automation.py -O main.py
```

4. **Перезапустите бота:**
```bash
systemctl restart telegram-bot
systemctl status telegram-bot
```

### Вариант 2: Ручная настройка

1. **Установите необходимые пакеты:**
```bash
apt update
apt install -y xvfb x11vnc fluxbox firefox-esr chromium-browser pulseaudio alsa-utils
```

2. **Создайте скрипт запуска с виртуальным дисплеем:**
```bash
cat > /opt/telegram-bot/start_with_display.sh << 'EOF'
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

chmod +x /opt/telegram-bot/start_with_display.sh
```

3. **Обновите systemd сервис:**
```bash
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
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart telegram-bot
```

## Проверка работы

1. **Проверьте статус бота:**
```bash
systemctl status telegram-bot
journalctl -u telegram-bot -f
```

2. **Отправьте ссылку на встречу боту в Telegram**

3. **Бот должен ответить:**
   - ✅ "Получил ссылку на встречу! Начинаю процесс автоматического присоединения..."
   - ⚠️ Если видите "Для автоматического присоединения нужно настроить виртуальный дисплей" - значит автоматизация не работает

## Поддерживаемые платформы встреч

- Zoom (zoom.us)
- Google Meet (meet.google.com)
- Microsoft Teams (teams.microsoft.com)
- Контур.Толк (ktalk.ru, talk.kontur.ru, 2a14p7ld.ktalk.ru)
- Яндекс Телемост (telemost.yandex.ru)

## Устранение неполадок

### Если бот не запускается:
```bash
journalctl -u telegram-bot -n 50
```

### Если GUI приложения не работают:
```bash
ps aux | grep Xvfb
echo $DISPLAY
```

### Если нет звука:
```bash
pulseaudio --check
pulseaudio --start
```

## Дополнительные возможности

После настройки виртуального дисплея бот сможет:
- ✅ Автоматически присоединяться к встречам
- ✅ Записывать аудио
- ✅ Делать скриншоты экрана
- ✅ Анализировать контент встречи
- ✅ Обновлять лиды в Bitrix24
