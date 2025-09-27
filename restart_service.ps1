# PowerShell скрипт для перезапуска сервиса
param(
    [string]$ServerHost = "109.172.47.253",
    [string]$ServerUser = "root",
    [string]$Password = "MmSS0JSm%6vb"
)

Write-Host "🔄 Перезапускаем сервис на сервере $ServerHost..." -ForegroundColor Green

# Функция для выполнения SSH команд через plink
function Invoke-PlinkCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    
    try {
        # Проверяем, есть ли plink
        $plinkPath = Get-Command plink -ErrorAction SilentlyContinue
        if (-not $plinkPath) {
            Write-Host "❌ plink не найден. Установите PuTTY или добавьте plink в PATH" -ForegroundColor Red
            return $false
        }
        
        # Выполняем команду через plink
        $result = & plink -ssh -l $ServerUser -pw $Password -o "StrictHostKeyChecking=no" $ServerHost $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description - успешно" -ForegroundColor Green
            if ($result) {
                Write-Host "   Вывод: $result" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "❌ $Description - ошибка (код: $LASTEXITCODE)" -ForegroundColor Red
            if ($result) {
                Write-Host "   Ошибка: $result" -ForegroundColor Red
            }
            return $false
        }
    } catch {
        Write-Host "💥 $Description - исключение: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Команды для перезапуска сервиса
$commands = @(
    @{
        Command = "systemctl stop meeting-bot.service"
        Description = "Остановка сервиса"
    },
    @{
        Command = "systemctl status meeting-bot.service --no-pager"
        Description = "Проверка статуса после остановки"
    },
    @{
        Command = "systemctl start meeting-bot.service"
        Description = "Запуск сервиса"
    },
    @{
        Command = "systemctl status meeting-bot.service --no-pager"
        Description = "Проверка статуса после запуска"
    },
    @{
        Command = "journalctl -u meeting-bot.service --no-pager -n 10"
        Description = "Проверка логов"
    }
)

# Выполнение команд
$successCount = 0
for ($i = 0; $i -lt $commands.Count; $i++) {
    $step = $i + 1
    $cmd = $commands[$i]
    
    if (Invoke-PlinkCommand -Command $cmd.Command -Description "$($cmd.Description) (шаг $step/$($commands.Count))") {
        $successCount++
    } else {
        Write-Host "❌ Перезапуск прерван на шаге $step" -ForegroundColor Red
        break
    }
}

# Результат
if ($successCount -eq $commands.Count) {
    Write-Host "🎉 Перезапуск завершен успешно!" -ForegroundColor Green
    Write-Host "🤖 Сервис должен быть запущен" -ForegroundColor Green
    Write-Host "📱 Попробуйте отправить боту сообщение" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Перезапуск завершен частично: $successCount/$($commands.Count) шагов" -ForegroundColor Yellow
}

Write-Host "`n💡 Для проверки запустите: .\check_bot.bat" -ForegroundColor Cyan
