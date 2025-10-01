@echo off
echo ========================================
echo   Upload Authorization Files to Server
echo ========================================
echo.

REM Get server details
set /p SERVER_IP="Enter server IP: "
set /p SERVER_USER="Enter server user (root): "
if "%SERVER_USER%"=="" set SERVER_USER=root

echo.
echo Uploading authorization files to %SERVER_USER%@%SERVER_IP%...
echo.

REM Upload main files
echo Uploading selenium_cookies.json...
scp selenium_cookies.json %SERVER_USER%@%SERVER_IP%:/opt/meeting-bot/

echo Uploading storage.json...
scp storage.json %SERVER_USER%@%SERVER_IP%:/opt/meeting-bot/

REM Upload all cookies files
echo Uploading cookies files...
scp cookies_*.json %SERVER_USER%@%SERVER_IP%:/opt/meeting-bot/

REM Upload all storage files
echo Uploading storage files...
scp storage_*.json %SERVER_USER%@%SERVER_IP%:/opt/meeting-bot/

echo.
echo ========================================
echo   Testing authorization on server...
echo ========================================

REM Test authorization on server
ssh %SERVER_USER%@%SERVER_IP% "cd /opt/meeting-bot && python3 check_auth.py"

echo.
echo ========================================
echo   Authorization upload complete!
echo ========================================
echo.
echo Bot should now be able to automatically login to:
echo - Google Meet
echo - Microsoft Teams  
echo - Zoom
echo - Yandex Telemost
echo.
pause
