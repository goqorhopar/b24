@echo off
echo 🔧 Переход в правильную директорию...
echo =====================================

echo Переход в папку проекта...
cd /d "C:\Users\PC\Downloads\гитхаб\b24"

echo Проверка текущей директории...
echo Текущая папка: %CD%

echo Проверка Git репозитория...
git status

echo.
echo ✅ Теперь вы в правильной директории!
echo Можете выполнить:
echo   git add .
echo   git commit -m "Add autonomous bot files and fix GitHub Actions workflow"
echo   git push origin main
echo.
pause
