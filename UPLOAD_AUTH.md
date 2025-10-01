# 🔐 Загрузка файлов авторизации на сервер

## 🚀 Быстрый способ

### Вариант 1: PowerShell (рекомендуется)
```powershell
.\upload_auth.ps1
```

### Вариант 2: Batch файл
```cmd
upload_auth.bat
```

### Вариант 3: Ручные команды
```bash
# Замените YOUR_SERVER_IP на IP вашего сервера
scp selenium_cookies.json root@YOUR_SERVER_IP:/opt/meeting-bot/
scp storage.json root@YOUR_SERVER_IP:/opt/meeting-bot/
scp cookies_*.json root@YOUR_SERVER_IP:/opt/meeting-bot/
scp storage_*.json root@YOUR_SERVER_IP:/opt/meeting-bot/
```

## 📋 Что происходит

1. **Проверка файлов** - убеждаемся, что файлы авторизации есть
2. **Копирование на сервер** - загружаем все файлы в `/opt/meeting-bot/`
3. **Тестирование** - проверяем, что авторизация работает на сервере

## 🎯 Результат

После загрузки бот сможет автоматически:
- ✅ Входить в Google Meet
- ✅ Входить в Microsoft Teams
- ✅ Входить в Zoom
- ✅ Входить в Яндекс Телемост

## 🔍 Проверка

После загрузки проверьте на сервере:
```bash
# Проверка файлов
ls -la /opt/meeting-bot/*.json

# Тест авторизации
cd /opt/meeting-bot && python3 check_auth.py

# Статус бота
systemctl status meeting-bot
```

## ⚠️ Важно

- Файлы авторизации **НЕ** попадают в Git репозиторий
- Они копируются **только** на сервер
- Безопасность данных сохранена
