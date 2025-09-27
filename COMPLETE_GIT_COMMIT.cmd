@echo off
echo Завершение Git коммита и загрузка в GitHub...
git commit -m "Add auto-deploy system"
git push origin main
echo Готово! Файлы загружены в GitHub.
echo Проверьте GitHub Actions в вашем репозитории.
pause
