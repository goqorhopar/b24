@echo off
REM ===========================================
REM АВТОМАТИЧЕСКИЙ КОММИТ ДЛЯ WINDOWS
REM ===========================================

echo 🔄 Автоматический коммит...

REM Проверяем есть ли изменения
git diff --quiet
if errorlevel 1 goto :has_changes
git diff --cached --quiet
if errorlevel 1 goto :has_changes

echo ℹ️ Нет изменений для коммита
exit /b 0

:has_changes
echo 📝 Есть изменения, создаю коммит...

REM Добавляем все изменения
git add .

REM Создаем коммит с текущим временем
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "commit_message=Auto commit: %YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"

git commit -m "%commit_message%"

if errorlevel 1 (
    echo ❌ Ошибка автоматического коммита
    exit /b 1
)

echo ✅ Автоматический коммит выполнен: %commit_message%

REM Запускаем автоматический деплой
echo 🚀 Запускаю автоматический деплой...
python auto_deploy.py --commit

if errorlevel 1 (
    echo ❌ Ошибка автоматического деплоя
    exit /b 1
)

echo ✅ Автоматический деплой выполнен
