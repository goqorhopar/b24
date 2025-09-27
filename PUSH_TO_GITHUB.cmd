@echo off
echo Загрузка файлов автоматического деплоя в GitHub...
git add .
git commit -m "Add auto-deploy system"
git push origin main
echo Готово! Файлы загружены в GitHub.
echo GitHub Actions автоматически задеплоит на сервер.
pause
