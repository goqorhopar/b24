# 🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ: ИЗМЕНЕНИЯ → GITHUB → СЕРВЕР

## 🎯 ЦЕЛЬ
Настроить автоматическую синхронизацию:
**Изменения файлов → GitHub → Автоматический деплой на сервер**

## 📋 ШАГ 1: НАСТРОЙКА ЛОКАЛЬНОГО РЕПОЗИТОРИЯ

### 1.1 Инициализация Git
```bash
# В папке с проектом
git init
git add .
git commit -m "Initial commit: Autonomous Meeting Bot"
```

### 1.2 Создание GitHub репозитория
1. Перейдите на https://github.com/new
2. Создайте новый репозиторий (например: `autonomous-meeting-bot`)
3. НЕ добавляйте README, .gitignore или лицензию

### 1.3 Подключение к GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/autonomous-meeting-bot.git
git branch -M main
git push -u origin main
```

## 📋 ШАГ 2: НАСТРОЙКА GITHUB ACTIONS

### 2.1 Создание SSH ключа на сервере
```bash
# На сервере (109.172.47.253)
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
cat /root/.ssh/id_rsa.pub
```

### 2.2 Добавление SSH ключа в GitHub
1. Скопируйте содержимое `/root/.ssh/id_rsa.pub`
2. Перейдите в GitHub → Settings → SSH and GPG keys
3. Нажмите "New SSH key"
4. Вставьте публичный ключ

### 2.3 Настройка GitHub Secrets
1. Перейдите в ваш репозиторий → Settings → Secrets and variables → Actions
2. Добавьте следующие секреты:

```
SERVER_HOST: 109.172.47.253
SERVER_USER: root
SERVER_SSH_KEY: [содержимое /root/.ssh/id_rsa]
```

## 📋 ШАГ 3: НАСТРОЙКА СЕРВЕРА

### 3.1 Клонирование репозитория на сервер
```bash
# На сервере
cd /root
git clone git@github.com:YOUR_USERNAME/autonomous-meeting-bot.git b24
cd b24
```

### 3.2 Установка зависимостей
```bash
pip3 install requests google-generativeai
```

### 3.3 Настройка systemd сервиса
```bash
chmod +x deploy_autonomous_server.sh
./deploy_autonomous_server.sh
```

## 🎯 РЕЗУЛЬТАТ: АВТОМАТИЧЕСКАЯ СИНХРОНИЗАЦИЯ

### ✅ Что происходит автоматически:

1. **Изменения файлов** → Git commit → Push в GitHub
2. **GitHub Actions** → Автоматический деплой на сервер
3. **Сервер** → Обновление бота → Перезапуск сервиса

### 🔄 Рабочий процесс:

1. **Вы изменяете файлы** (например, `autonomous_server_bot.py`)
2. **Git commit и push:**
   ```bash
   git add .
   git commit -m "Update bot functionality"
   git push origin main
   ```
3. **GitHub Actions автоматически:**
   - Подключается к серверу
   - Останавливает старый бот
   - Обновляет код с GitHub
   - Устанавливает зависимости
   - Запускает обновленный бот

### 📱 Проверка работы:

1. **Статус GitHub Actions:**
   - Перейдите в ваш репозиторий → Actions
   - Проверьте статус последнего деплоя

2. **Статус бота на сервере:**
   ```bash
   systemctl status meeting-bot-autonomous.service
   journalctl -u meeting-bot-autonomous.service -f
   ```

3. **Тест в Telegram:**
   - Отправьте `/status` боту
   - Проверьте что бот отвечает

## 🚀 КОМАНДЫ ДЛЯ БЫСТРОГО СТАРТА

### Локально:
```bash
# Изменения файлов
git add .
git commit -m "Update bot"
git push origin main
```

### На сервере:
```bash
# Проверка статуса
systemctl status meeting-bot-autonomous.service

# Просмотр логов
journalctl -u meeting-bot-autonomous.service -f

# Ручное обновление (если нужно)
cd /root/b24
git pull origin main
systemctl restart meeting-bot-autonomous.service
```

## 🎉 ИТОГ

**АВТОМАТИЧЕСКАЯ СИНХРОНИЗАЦИЯ НАСТРОЕНА!**

- ✅ Изменения файлов → GitHub
- ✅ GitHub → Автоматический деплой на сервер  
- ✅ Бот обновляется без вашего участия
- ✅ Работает 24/7 автономно
- ✅ Автоматический перезапуск при сбоях

**НИКАКОГО РУЧНОГО ВМЕШАТЕЛЬСТВА НЕ ТРЕБУЕТСЯ!**
