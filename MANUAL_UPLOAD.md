# Ручная загрузка файлов на сервер

## Вариант 1: WinSCP (рекомендуется)

1. **Скачай WinSCP**: https://winscp.net/eng/download.php
2. **Подключись к серверу:**
   - Host: `109.172.47.253`
   - Username: `root`
   - Password: `MmSS0JSm%6vb`
3. **Загрузи файлы в `/root/b24/`:**
   - `meeting-bot.py`
   - `monitor_bot.py`
   - `load_auth_data.py`
   - `meeting_bot_playwright.py`
   - `install_server.sh`
   - `bot_control.sh`
   - `server_commands.sh`
   - `meeting-bot.service`
   - `meeting-bot-monitor.service`
   - `requirements.txt`
   - `selenium_cookies.json` (если есть)
   - `storage.json` (если есть)

## Вариант 2: FileZilla

1. **Скачай FileZilla**: https://filezilla-project.org/
2. **Подключись к серверу** (те же данные)
3. **Загрузи файлы** в `/root/b24/`

## Вариант 3: Командная строка (если есть sshpass)

```bash
# Установи sshpass
# На Ubuntu: sudo apt install sshpass
# На Windows: используй WSL

# Загрузи файлы
sshpass -p "MmSS0JSm%6vb" scp meeting-bot.py root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp monitor_bot.py root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp load_auth_data.py root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp meeting_bot_playwright.py root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp install_server.sh root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp bot_control.sh root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp server_commands.sh root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp meeting-bot.service root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp meeting-bot-monitor.service root@109.172.47.253:/root/b24/
sshpass -p "MmSS0JSm%6vb" scp requirements.txt root@109.172.47.253:/root/b24/
```

## После загрузки на сервере:

```bash
# Подключись к серверу
ssh root@109.172.47.253

# Перейди в директорию
cd /root/b24

# Сделай скрипты исполняемыми
chmod +x *.sh

# Запусти установку
./install_server.sh

# Настрой .env файл (добавь TELEGRAM_BOT_TOKEN)
nano .env

# Запусти бота
systemctl start meeting-bot
systemctl enable meeting-bot
systemctl start meeting-bot-monitor
systemctl enable meeting-bot-monitor

# Проверь статус
systemctl status meeting-bot
systemctl status meeting-bot-monitor
```

## Проверка работы:

```bash
# Посмотри логи
journalctl -u meeting-bot -f

# Проверь статус
./server_commands.sh
```

**Рекомендую использовать WinSCP - самый простой способ!**
