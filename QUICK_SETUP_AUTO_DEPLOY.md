# 🚀 БЫСТРАЯ НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ

## 🎯 ЦЕЛЬ
**Изменения файлов → GitHub → Автоматический деплой на сервер**

## 📋 ШАГ 1: СОЗДАНИЕ GITHUB РЕПОЗИТОРИЯ

1. Перейдите на https://github.com/new
2. Создайте репозиторий: `autonomous-meeting-bot`
3. НЕ добавляйте README, .gitignore, лицензию

## 📋 ШАГ 2: НАСТРОЙКА ЛОКАЛЬНОГО РЕПОЗИТОРИЯ

### В командной строке Windows (cmd):
```cmd
cd C:\Users\PC\Downloads\гитхаб\b24
git init
git add .
git commit -m "Initial commit: Autonomous Meeting Bot"
git remote add origin https://github.com/YOUR_USERNAME/autonomous-meeting-bot.git
git branch -M main
git push -u origin main
```

## 📋 ШАГ 3: НАСТРОЙКА GITHUB SECRETS

1. Перейдите в ваш репозиторий → Settings → Secrets and variables → Actions
2. Добавьте секреты:

```
SERVER_HOST: 109.172.47.253
SERVER_USER: root
SERVER_SSH_KEY: [приватный SSH ключ с сервера]
```

## 📋 ШАГ 4: НАСТРОЙКА СЕРВЕРА

### На сервере (109.172.47.253):
```bash
# Создание SSH ключа
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
cat /root/.ssh/id_rsa.pub
```

### Добавьте публичный ключ в GitHub:
1. Скопируйте содержимое `/root/.ssh/id_rsa.pub`
2. GitHub → Settings → SSH and GPG keys → New SSH key
3. Вставьте публичный ключ

### Клонирование репозитория на сервер:
```bash
cd /root
git clone git@github.com:YOUR_USERNAME/autonomous-meeting-bot.git b24
cd b24
pip3 install requests google-generativeai
chmod +x deploy_autonomous_server.sh
./deploy_autonomous_server.sh
```

## 🎯 РЕЗУЛЬТАТ: АВТОМАТИЧЕСКАЯ СИНХРОНИЗАЦИЯ

### ✅ Рабочий процесс:

1. **Вы изменяете файлы** (например, `autonomous_server_bot.py`)
2. **Git commit и push:**
   ```cmd
   git add .
   git commit -m "Update bot"
   git push origin main
   ```
3. **GitHub Actions автоматически:**
   - Подключается к серверу
   - Останавливает старый бот
   - Обновляет код с GitHub
   - Запускает обновленный бот

### 📱 Проверка:

1. **GitHub Actions:** Репозиторий → Actions → Проверить статус
2. **Сервер:** `systemctl status meeting-bot-autonomous.service`
3. **Telegram:** Отправить `/status` боту

## 🚀 КОМАНДЫ ДЛЯ ОБНОВЛЕНИЯ

### После изменения файлов:
```cmd
git add .
git commit -m "Update bot functionality"
git push origin main
```

**ВСЁ! Бот автоматически обновится на сервере!**

## 🎉 ИТОГ

**АВТОМАТИЧЕСКАЯ СИНХРОНИЗАЦИЯ:**
- ✅ Изменения файлов → GitHub
- ✅ GitHub → Автоматический деплой на сервер
- ✅ Бот обновляется без вашего участия
- ✅ Работает 24/7 автономно

**НИКАКОГО РУЧНОГО ВМЕШАТЕЛЬСТВА НЕ ТРЕБУЕТСЯ!**
