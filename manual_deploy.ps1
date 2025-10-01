# Ручная загрузка файлов на сервер через PowerShell
Write-Host "=== Ручная загрузка Meeting Bot на сервер ===" -ForegroundColor Green

# Параметры сервера
$SERVER = "109.172.47.253"
$USER = "root"
$PASSWORD = "MmSS0JSm%6vb"
$REMOTE_DIR = "/root/b24"

Write-Host "Подключение к серверу $SERVER..." -ForegroundColor Yellow

# Устанавливаем sshpass если нужно
if (-not (Get-Command sshpass -ErrorAction SilentlyContinue)) {
    Write-Host "Установите sshpass для Windows или используйте WSL" -ForegroundColor Red
    Write-Host "Альтернатива: используйте WinSCP или FileZilla" -ForegroundColor Yellow
    exit 1
}

# Создаем директорию на сервере
Write-Host "Создание директории на сервере..." -ForegroundColor Yellow
& sshpass -p $PASSWORD ssh -o StrictHostKeyChecking=no "${USER}@${SERVER}" "mkdir -p $REMOTE_DIR"

# Загружаем основные файлы
Write-Host "Загрузка основных файлов..." -ForegroundColor Yellow

$files = @(
    "meeting-bot.py",
    "monitor_bot.py", 
    "load_auth_data.py",
    "meeting_bot_playwright.py",
    "install_server.sh",
    "bot_control.sh",
    "server_commands.sh",
    "meeting-bot.service",
    "meeting-bot-monitor.service",
    "requirements.txt"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Загружаю $file..." -ForegroundColor Cyan
        & sshpass -p $PASSWORD scp -o StrictHostKeyChecking=no $file "${USER}@${SERVER}:${REMOTE_DIR}/"
    } else {
        Write-Host "Файл $file не найден!" -ForegroundColor Red
    }
}

# Загружаем файлы авторизации (если есть)
$authFiles = @("selenium_cookies.json", "storage.json")
foreach ($file in $authFiles) {
    if (Test-Path $file) {
        Write-Host "Загружаю $file..." -ForegroundColor Cyan
        & sshpass -p $PASSWORD scp -o StrictHostKeyChecking=no $file "${USER}@${SERVER}:${REMOTE_DIR}/"
    }
}

Write-Host "=== Загрузка завершена ===" -ForegroundColor Green
Write-Host ""
Write-Host "Теперь на сервере выполни:" -ForegroundColor Yellow
Write-Host "cd /root/b24" -ForegroundColor White
Write-Host "chmod +x *.sh" -ForegroundColor White
Write-Host "./install_server.sh" -ForegroundColor White
