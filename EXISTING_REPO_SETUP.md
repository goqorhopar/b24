# 🔧 НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ ДЛЯ СУЩЕСТВУЮЩЕГО РЕПОЗИТОРИЯ

## 🎯 ЦЕЛЬ
Настроить автоматический деплой для вашего существующего GitHub репозитория.

## 📋 ШАГ 1: НАСТРОЙКА ЛОКАЛЬНОГО РЕПОЗИТОРИЯ

### 1.1 Добавление файлов в Git
```bash
# В папке с проектом
git add .
git commit -m "Add auto-deploy system"
git push origin main
```

## 📋 ШАГ 2: НАСТРОЙКА GITHUB SECRETS

### 2.1 Перейдите в ваш репозиторий на GitHub
1. Откройте ваш репозиторий
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"

### 2.2 Добавьте следующие секреты:

```
SERVER_HOST: 109.172.47.253
SERVER_USER: root
SERVER_SSH_KEY: [приватный SSH ключ с сервера]
```

## 📋 ШАГ 3: НАСТРОЙКА СЕРВЕРА

### 3.1 Создание SSH ключа на сервере
```bash
# На сервере (109.172.47.253)
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
cat /root/.ssh/id_rsa.pub
```

### 3.2 Добавление публичного ключа в GitHub
1. Скопируйте содержимое `/root/.ssh/id_rsa.pub`
2. GitHub → Settings → SSH and GPG keys → New SSH key
3. Вставьте публичный ключ

### 3.3 Добавление приватного ключа в GitHub Secrets
1. Скопируйте содержимое `/root/.ssh/id_rsa`
2. GitHub → Repository → Settings → Secrets → Actions
3. Создайте секрет `SERVER_SSH_KEY` с содержимым приватного ключа

### 3.4 Клонирование репозитория на сервер
```bash
# На сервере
cd /root
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git b24
cd b24
pip3 install requests google-generativeai
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
