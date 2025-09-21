# 🎉 Meeting Bot - Полная автоматизация деплоя

## 🚀 Что получилось

Создана **полностью автоматизированная система** для Meeting Bot, которая:

- ✅ **Автоматически коммитит** все изменения в GitHub
- ✅ **Деплоит на сервер** при каждом push
- ✅ **Отправляет уведомления** в Telegram
- ✅ **Проверяет работоспособность** после деплоя
- ✅ **Откатывается** при ошибках

## ⚡ БЫСТРЫЙ СТАРТ (3 шага)

### 1. Настройка (один раз)

```bash
# Запустите финальную настройку
python FINAL_AUTO_DEPLOY_SETUP.py
```

### 2. Заполните .env файл

```env
# ОБЯЗАТЕЛЬНО
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyABCdefGHIjklMNOpqrsTUVwxyz123456

# GitHub
GITHUB_REPO=yourusername/meeting-bot
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Сервер
DEPLOY_SERVER_URL=192.168.1.100
DEPLOY_SERVER_USER=root
DEPLOY_SERVER_PATH=/opt/meeting-bot

# Уведомления
ADMIN_CHAT_ID=123456789
```

### 3. Запустите деплой

```bash
# Windows
deploy_automation.bat

# Linux/Mac
./quick_deploy.sh
```

## 🔄 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ

После настройки **ВСЕ изменения автоматически деплоятся**:

```bash
# Любые изменения в коде
git add .
git commit -m "Update bot"
git push origin main

# 🚀 Автоматически:
# 1. GitHub Actions запускается
# 2. Код деплоится на сервер
# 3. Сервис перезапускается
# 4. Отправляется уведомление в Telegram
```

## 📁 Созданные файлы

### Основные файлы
- `auto_deploy.py` - Система автоматического деплоя
- `quick_deploy.sh` - Быстрый деплой (Linux/Mac)
- `deploy_automation.bat` - Быстрый деплой (Windows)
- `setup_auto_deploy.sh` - Настройка (Linux/Mac)
- `setup_auto_deploy.bat` - Настройка (Windows)

### Конфигурация
- `env_example.txt` - Пример конфигурации (ОБНОВЛЕН)
- `.github/workflows/auto-deploy.yml` - GitHub Actions

### Документация
- `README_AUTO_DEPLOY.md` - Основное руководство
- `AUTO_DEPLOY_GUIDE.md` - Подробная документация
- `DEPLOY_SETUP_COMPLETE.md` - Инструкции после настройки

### Серверные файлы
- `server_meeting_bot.py` - Основной класс серверного бота
- `main_server_bot.py` - Главный файл с Telegram ботом
- `server_config.py` - Конфигурация для сервера
- `requirements_simple.txt` - Зависимости Python
- `Dockerfile.server` - Docker контейнер
- `docker-compose.server.yml` - Docker Compose

## 🎯 Возможности бота

### Автоматизация встреч
- ✅ **Присоединение** к встречам как "Асистент Григория"
- ✅ **Поддержка платформ**: Zoom, Google Meet, Teams, Контур.Толк, Яндекс.Телемост
- ✅ **Запись аудио** с системного звука
- ✅ **Транскрипция** через Whisper AI
- ✅ **Анализ встреч** через Gemini AI по чек-листу

### Интеграция с Bitrix24
- ✅ **Обновление лидов** автоматически
- ✅ **Создание задач** (минимум 3)
- ✅ **Заполнение полей** из анализа встречи
- ✅ **Комментарии** в истории лида

### Серверное развертывание
- ✅ **Headless режим** для работы на сервере
- ✅ **Docker поддержка**
- ✅ **Мониторинг и логирование**
- ✅ **Автоматический перезапуск**

## 📱 Уведомления

Бот отправляет уведомления в Telegram:

- ✅ **Успешный деплой** - "Деплой завершен успешно!"
- ❌ **Ошибка деплоя** - "Ошибка деплоя на сервер"
- 📊 **Статистика встреч** - "Обработано 5 встреч"
- 🔧 **Системные события** - "Сервис перезапущен"

## 🛠️ Команды

### Основные команды

```bash
# Полный деплой (коммит + деплой)
python auto_deploy.py

# Только коммит в GitHub
python auto_deploy.py --commit

# Только деплой на сервер
python auto_deploy.py --deploy

# Проверка статуса
python auto_deploy.py --status

# Настройка автоматического деплоя
python auto_deploy.py --setup
```

### Скрипты

```bash
# Быстрый деплой
./quick_deploy.sh          # Linux/Mac
deploy_automation.bat      # Windows

# Настройка
./setup_auto_deploy.sh     # Linux/Mac
setup_auto_deploy.bat      # Windows

# Финальная настройка
python FINAL_AUTO_DEPLOY_SETUP.py
```

## 🔍 Мониторинг

### Проверка статуса

```bash
# Статус сервиса
ssh user@server 'systemctl status meeting-bot'

# Логи сервиса
ssh user@server 'journalctl -u meeting-bot -f'

# Логи деплоя
tail -f auto_deploy.log

# GitHub Actions
# Перейдите в репозиторий → Actions
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Ошибка SSH подключения

```bash
# Проверьте SSH ключи
ssh -T git@github.com
ssh user@your_server

# Проверьте права
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

#### 2. Ошибка GitHub токена

```bash
# Проверьте токен
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

#### 3. Ошибка деплоя на сервер

```bash
# Проверьте доступ
ssh user@server 'whoami'

# Проверьте права
ssh user@server 'ls -la /opt/meeting-bot'

# Проверьте сервис
ssh user@server 'systemctl status meeting-bot'
```

#### 4. Откат к предыдущей версии

```bash
# На сервере
ssh user@server
cd /opt/meeting-bot
git log --oneline -10
git reset --hard COMMIT_HASH
systemctl restart meeting-bot
```

## 📊 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Локальная     │    │     GitHub      │    │     Сервер      │
│   разработка    │    │                 │    │                 │
│                 │    │                 │    │                 │
│ 1. Изменения    │───▶│ 2. GitHub       │───▶│ 3. Автоматический│
│    в коде       │    │    Actions      │    │    деплой       │
│                 │    │                 │    │                 │
│ 4. Уведомления  │◀───│ 5. Webhook      │◀───│ 6. Статус       │
│    в Telegram   │    │    уведомления  │    │    сервиса      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔒 Безопасность

### Рекомендации

1. **Используйте отдельного пользователя** для деплоя
2. **Ограничьте права** SSH ключей
3. **Регулярно обновляйте** токены
4. **Мониторьте логи** на предмет подозрительной активности

### Настройка пользователя для деплоя

```bash
# Создаем пользователя
sudo useradd -m -s /bin/bash deployer

# Добавляем в группу sudo
sudo usermod -aG sudo deployer

# Настраиваем SSH ключи
sudo -u deployer ssh-keygen -t rsa -b 4096

# Копируем публичный ключ на сервер
sudo -u deployer ssh-copy-id deployer@your_server
```

## 📈 Расширенные настройки

### Множественные серверы

```env
# В .env можно указать несколько серверов
DEPLOY_SERVER_URL=server1.com,server2.com,server3.com
DEPLOY_SERVER_USER=deployer,deployer,deployer
```

### Кастомные команды

```env
# Команда перед деплоем
DEPLOY_PRE_COMMAND=systemctl stop nginx

# Команда после деплоя
DEPLOY_POST_COMMAND=systemctl start nginx
```

### Уведомления в Slack

```env
# Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 📚 Документация

- [📖 Основное руководство](README_AUTO_DEPLOY.md)
- [🔧 Подробная документация](AUTO_DEPLOY_GUIDE.md)
- [🖥️ Настройка сервера](SERVER_DEPLOYMENT_GUIDE.md)
- [🐳 Docker деплой](docker-compose.server.yml)
- [⚡ Быстрый старт](QUICK_START_SERVER.md)
- [📋 Инструкции после настройки](DEPLOY_SETUP_COMPLETE.md)

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f auto_deploy.log`
2. Проверьте GitHub Actions
3. Проверьте статус сервиса на сервере
4. Создайте issue в репозитории

## 🎉 Готово!

Теперь у вас есть **полностью автоматизированная система**:

- ✅ **Любые изменения в коде автоматически попадают на сервер**
- ✅ **Получаете уведомления о статусе деплоя**
- ✅ **Можете откатиться к любой версии**
- ✅ **Система мониторит работоспособность**

**Просто работайте с кодом, а деплой происходит автоматически!** 🚀

---

## 🚀 Следующие шаги

1. **Запустите настройку**: `python FINAL_AUTO_DEPLOY_SETUP.py`
2. **Заполните .env файл** с вашими данными
3. **Настройте GitHub Secrets**
4. **Запустите деплой**: `./quick_deploy.sh` или `deploy_automation.bat`
5. **Наслаждайтесь автоматическим деплоем!** 🎉