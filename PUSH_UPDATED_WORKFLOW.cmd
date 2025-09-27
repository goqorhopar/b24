@echo off
echo 🔧 Обновление GitHub Actions workflow...
echo =====================================

echo Добавление изменений в Git...
git add .github/workflows/auto-deploy.yml

echo Коммит изменений...
git commit -m "Fix GitHub Actions workflow - use existing VPS secrets"

echo Пуш в GitHub...
git push origin main

echo.
echo ✅ GitHub Actions workflow обновлен!
echo Теперь используется ваши существующие секреты:
echo - VPS_HOST
echo - VPS_USERNAME  
echo - VPS_SSH_KEY
echo.
echo Проверьте GitHub Actions: https://github.com/goqorhopar/b24/actions
echo.
pause
