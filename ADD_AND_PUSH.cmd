@echo off
echo 🔧 Добавление всех файлов в Git...
echo =================================

echo Добавление всех изменений...
git add .

echo Коммит изменений...
git commit -m "Add autonomous bot files and fix GitHub Actions workflow"

echo Пуш в GitHub...
git push origin main

echo.
echo ✅ Все файлы добавлены и запушены!
echo GitHub Actions должен запуститься автоматически.
echo.
echo Проверьте: https://github.com/goqorhopar/b24/actions
echo.
pause
