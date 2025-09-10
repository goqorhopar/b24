# Основной веб-процесс для Render/Heroku
web: gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class sync --max-requests 1000 --max-requests-jitter 100 --preload --access-logfile - --error-logfile -

# Альтернативный запуск для отладки (закомментирован)
# web: python main.py

# Дополнительные процессы (если нужны)
worker: python worker.py
scheduler: python scheduler.py
release: python migrate.pyweb: gunicorn main:app --bind 0.0.0.0:$PORT
