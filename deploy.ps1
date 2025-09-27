# PowerShell скрипт для деплоя на сервер
param(
    [string]$ServerHost = "109.172.47.253",
    [string]$ServerUser = "root"
)

Write-Host "🚀 Начинаем деплой на сервер $ServerHost..." -ForegroundColor Green

# Функция для выполнения SSH команд
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    
    try {
        $result = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$ServerUser@$ServerHost" $Command
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description - успешно" -ForegroundColor Green
            if ($result) {
                Write-Host "   Вывод: $result" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "❌ $Description - ошибка (код: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "💥 $Description - исключение: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Команды для деплоя
$commands = @(
    @{
        Command = "systemctl stop meeting-bot.service || true"
        Description = "Остановка сервиса"
    },
    @{
        Command = "rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*"
        Description = "Очистка места"
    },
    @{
        Command = "cd /root/b24 && git pull origin main"
        Description = "Обновление кода из GitHub"
    },
    @{
        Command = @"
cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF
"@
        Description = "Создание .env файла"
    },
    @{
        Command = "cd /root/b24 && source venv/bin/activate && pip install -r requirements.txt"
        Description = "Установка зависимостей"
    },
    @{
        Command = @"
cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/b24
ExecStart=/root/b24/venv/bin/python /root/b24/main.py
Restart=always
RestartSec=10
Environment=LOG_LEVEL=INFO
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=USE_POLLING=true
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=BITRIX_USER_ID=1
Environment=DATABASE_URL=sqlite:///bot_state.db

[Install]
WantedBy=multi-user.target
EOF
"@
        Description = "Обновление systemd сервиса"
    },
    @{
        Command = "systemctl daemon-reload && systemctl enable meeting-bot.service && systemctl start meeting-bot.service"
        Description = "Перезапуск сервиса"
    },
    @{
        Command = "systemctl status meeting-bot.service --no-pager"
        Description = "Проверка статуса"
    }
)

# Выполнение команд
$successCount = 0
for ($i = 0; $i -lt $commands.Count; $i++) {
    $step = $i + 1
    $cmd = $commands[$i]
    
    if (Invoke-SSHCommand -Command $cmd.Command -Description "$($cmd.Description) (шаг $step/$($commands.Count))") {
        $successCount++
    } else {
        Write-Host "❌ Деплой прерван на шаге $step" -ForegroundColor Red
        break
    }
}

# Результат
if ($successCount -eq $commands.Count) {
    Write-Host "🎉 Деплой завершен успешно!" -ForegroundColor Green
    Write-Host "🤖 Бот должен быть запущен на сервере" -ForegroundColor Green
} else {
    Write-Host "⚠️  Деплой завершен частично: $successCount/$($commands.Count) шагов" -ForegroundColor Yellow
}

Write-Host "`n📋 Для проверки работы бота отправьте ему сообщение в Telegram" -ForegroundColor Cyan
