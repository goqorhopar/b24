# Upload Authorization Files to Server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Upload Authorization Files to Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get server details
$SERVER_IP = Read-Host "Enter server IP"
$SERVER_USER = Read-Host "Enter server user (root)"
if ([string]::IsNullOrEmpty($SERVER_USER)) { $SERVER_USER = "root" }

Write-Host ""
Write-Host "Uploading authorization files to $SERVER_USER@$SERVER_IP..." -ForegroundColor Yellow
Write-Host ""

# Check if files exist
$requiredFiles = @("selenium_cookies.json", "storage.json")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "ERROR: $file not found!" -ForegroundColor Red
        Write-Host "Run: python simple_auth.py" -ForegroundColor Yellow
        exit 1
    }
}

try {
    # Upload main files
    Write-Host "Uploading selenium_cookies.json..." -ForegroundColor Green
    scp selenium_cookies.json "${SERVER_USER}@${SERVER_IP}:/opt/meeting-bot/"

    Write-Host "Uploading storage.json..." -ForegroundColor Green
    scp storage.json "${SERVER_USER}@${SERVER_IP}:/opt/meeting-bot/"

    # Upload all cookies files
    Write-Host "Uploading cookies files..." -ForegroundColor Green
    Get-ChildItem "cookies_*.json" | ForEach-Object {
        scp $_.Name "${SERVER_USER}@${SERVER_IP}:/opt/meeting-bot/"
    }

    # Upload all storage files
    Write-Host "Uploading storage files..." -ForegroundColor Green
    Get-ChildItem "storage_*.json" | ForEach-Object {
        scp $_.Name "${SERVER_USER}@${SERVER_IP}:/opt/meeting-bot/"
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Testing authorization on server..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Test authorization on server
    ssh "${SERVER_USER}@${SERVER_IP}" "cd /opt/meeting-bot && python3 check_auth.py"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   Authorization upload complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Bot should now be able to automatically login to:" -ForegroundColor Yellow
    Write-Host "- Google Meet" -ForegroundColor White
    Write-Host "- Microsoft Teams" -ForegroundColor White
    Write-Host "- Zoom" -ForegroundColor White
    Write-Host "- Yandex Telemost" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "ERROR: Upload failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to continue"
