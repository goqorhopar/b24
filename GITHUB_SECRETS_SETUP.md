# 🔧 НАСТРОЙКА GITHUB SECRETS ДЛЯ АВТОМАТИЧЕСКОГО ДЕПЛОЯ

## ✅ ФАЙЛЫ ЗАГРУЖЕНЫ В GITHUB!

Теперь нужно настроить GitHub Secrets чтобы GitHub Actions мог подключиться к серверу.

## 📋 ШАГ 1: ПЕРЕЙДИТЕ В НАСТРОЙКИ РЕПОЗИТОРИЯ

1. Откройте ваш репозиторий: https://github.com/goqorhopar/b24
2. Нажмите **Settings** (вкладка справа)
3. В левом меню найдите **Secrets and variables** → **Actions**
4. Нажмите **New repository secret**

## 📋 ШАГ 2: ДОБАВЬТЕ СЛЕДУЮЩИЕ СЕКРЕТЫ

### Секрет 1: SERVER_HOST
- **Name:** `SERVER_HOST`
- **Secret:** `109.172.47.253`

### Секрет 2: SERVER_USER
- **Name:** `SERVER_USER`
- **Secret:** `root`

### Секрет 3: SERVER_SSH_KEY
- **Name:** `SERVER_SSH_KEY`
- **Secret:** [приватный SSH ключ с сервера]

## 📋 ШАГ 3: ПОЛУЧИТЕ SSH КЛЮЧ С СЕРВЕРА

### На сервере (109.172.47.253):
```bash
# Если SSH ключ уже есть:
cat /root/.ssh/id_rsa

# Если SSH ключа нет, создайте:
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
cat /root/.ssh/id_rsa
```

### Скопируйте ВЕСЬ вывод команды `cat /root/.ssh/id_rsa` (включая `-----BEGIN OPENSSH PRIVATE KEY-----` и `-----END OPENSSH PRIVATE KEY-----`)

## 📋 ШАГ 4: ДОБАВЬТЕ ПУБЛИЧНЫЙ КЛЮЧ В GITHUB

### На сервере:
```bash
cat /root/.ssh/id_rsa.pub
```

### В GitHub:
1. Перейдите в **Settings** → **SSH and GPG keys**
2. Нажмите **New SSH key**
3. Вставьте содержимое `/root/.ssh/id_rsa.pub`

## 📋 ШАГ 5: ЗАПУСТИТЕ GITHUB ACTIONS

### Вариант 1: Автоматически
- Сделайте любой коммит в main ветку
- GitHub Actions запустится автоматически

### Вариант 2: Вручную
1. Перейдите в **Actions** вкладку
2. Найдите workflow "Auto Deploy to Server"
3. Нажмите **Run workflow**

## 🎯 РЕЗУЛЬТАТ:

После настройки секретов:
1. ✅ GitHub Actions сможет подключиться к серверу
2. ✅ Автоматический деплой будет работать
3. ✅ Бот обновится на сервере
4. ✅ Все изменения будут автоматически синхронизироваться

## 🚀 ПРОВЕРКА:

1. **GitHub Actions:** Репозиторий → Actions → Проверить статус
2. **Сервер:** `systemctl status meeting-bot-autonomous.service`
3. **Telegram:** Отправить `/status` боту

## 🎉 ИТОГ:

**НАСТРОЙТЕ GITHUB SECRETS И ВСЁ ЗАРАБОТАЕТ!**
