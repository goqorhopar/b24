# Базовый образ Node.js
FROM node:20-alpine

# Установка curl для healthcheck
RUN apk add --no-cache curl

# Рабочая директория
WORKDIR /app

# Копируем package.json
COPY package.json ./

# Устанавливаем зависимости (только production) - работает без package-lock.json
RUN npm install --only=production --no-package-lock

# Копируем исходный код
COPY src ./src

# Переменные окружения
ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Открываем порт
EXPOSE 3000

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Команда запуска приложения
CMD ["node", "src/index.js"]
